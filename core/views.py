import json
import os
import logging
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import StreamingHttpResponse, JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Trip, ItineraryItem, ChatSession, Payment
from .forms import SignupForm
from services.image_engine.engine import ImageRetrievalService

logger = logging.getLogger('agent')


def landing(request):
    return render(request, 'landing.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'auth/signup.html', {'form': form})


@login_required
def dashboard(request):
    trips = Trip.objects.filter(user=request.user).exclude(status='archived')[:10]
    hour = timezone.localtime().hour
    if hour < 12:
        greeting = 'Good morning'
    elif hour < 17:
        greeting = 'Good afternoon'
    else:
        greeting = 'Good evening'
    
    # Stats
    total_trips = Trip.objects.filter(user=request.user).exclude(status='archived').count()
    this_month = Trip.objects.filter(
        user=request.user,
        created_at__month=timezone.now().month,
        created_at__year=timezone.now().year
    ).count()
    from django.db.models import Avg
    avg_budget = Trip.objects.filter(
        user=request.user
    ).exclude(status='archived').exclude(budget_inr=0).aggregate(
        avg=Avg('budget_inr')
    )['avg'] or 0
    
    return render(request, 'dashboard.html', {
        'trips': trips,
        'greeting': greeting,
        'total_trips': total_trips,
        'this_month': this_month,
        'avg_budget': int(avg_budget),
    })


@login_required
def chat_page(request):
    session, _ = ChatSession.objects.get_or_create(
        user=request.user,
        trip=None,
        defaults={'messages': [], 'graph_state': {}}
    )
    example_prompts = [
        'Goa 5 days 60k beaches and food',
        'Kerala 7 days family backwaters 80k',
        'Manali 4 days adventure trekking 50k',
        'Rajasthan 6 days honeymoon heritage 90k',
    ]
    return render(request, 'chat.html', {
        'session': session,
        'example_prompts': example_prompts,
    })


@login_required
@require_POST
async def chat_send(request):
    from asgiref.sync import sync_to_async
    user_msg = request.POST.get('message', '').strip()
    session_id = request.POST.get('session_id', '')
    
    if not user_msg:
        return StreamingHttpResponse('', content_type='text/html')
    
    @sync_to_async
    def get_session():
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.messages.append({'role': 'user', 'content': user_msg})
        session.save()
        return session

    session = await get_session()
    
    async def generate():
        yield "<div class='msg msg-ai'><span class='ai-label'>TripMind</span><span class='ai-text'>"
        
        try:
            from agent.core.context import PlanningContext
            from agent.core.executor import DAGExecutor
            from core.models import UserProfile, Trip, TripVersion, ItineraryItem
            
            @sync_to_async
            def setup_context():
                up, _ = UserProfile.objects.get_or_create(user=request.user)
                up.preferences['last_message'] = user_msg
                context = PlanningContext(user_profile=up)
                if session.graph_state:
                    context.destination = session.graph_state.get('destination', '')
                return context, up

            context, up = await setup_context()
            executor = DAGExecutor()
            
            # Stream progress updates from the DAG
            async for progress_msg in executor.run_dag(context):
                # Yield HTML fragments that simulate streaming text or status
                yield f"<div class='status-update' style='font-size: 0.8rem; color: var(--text-muted);'><i class='bi bi-arrow-repeat spin'></i> {progress_msg}</div>"
            
            # DAG finished. Extract final results
            final_itinerary = context.get_api_result("final_itinerary")
            final_error = context.get_api_result("final_error")
            clarification = context.get_api_result("clarification")
            
            if clarification:
                response_text = clarification
                yield f"<div>{response_text}</div>"
            elif final_error:
                response_text = "I encountered an error: " + final_error
                yield f"<div>{response_text}</div>"
            elif final_itinerary:
                response_text = "Your itinerary is ready!"
                yield f"<div>{response_text}</div>"
                
                @sync_to_async
                def save_trip():
                    # Simplified db save
                    trip = session.trip
                    if not trip:
                        trip = Trip.objects.create(
                            user=request.user,
                            destination=context.destination,
                            num_days=context.budget.total_days if context.budget else 3,
                            budget_inr=context.budget.total_budget if context.budget else 0,
                            category=up.preferences.get('category', 'general')
                        )
                        session.trip = trip
                    
                    v_num = TripVersion.objects.filter(trip=trip).count() + 1
                    version = TripVersion.objects.create(trip=trip, version_number=v_num, itinerary_json=final_itinerary)
                    
                    items = []
                    for day in final_itinerary:
                        for slot in day.get('slots', []):
                            items.append(ItineraryItem(
                                version=version,
                                day_number=day.get('day', 1),
                                start_time=slot.get('start_time', '09:00'),
                                end_time=slot.get('end_time', '10:00'),
                                place_name=slot.get('place', ''),
                                place_type=slot.get('type', 'attraction'),
                                cost_inr=slot.get('cost_inr', 0),
                                visual_metadata=slot.get('visual')
                            ))
                    ItineraryItem.objects.bulk_create(items)
                    
                    session.graph_state['destination'] = context.destination
                    session.messages.append({'role': 'assistant', 'content': response_text})
                    session.save()
                    return trip
                    
                trip = await save_trip()
                yield (
                    f"<div class='plan-ready-btn'>"
                    f"<a href='/trips/{trip.pk}/' "
                    f"class='btn btn-primary btn-sm mt-2'>View Full Itinerary →</a>"
                    f"</div>"
                )
            else:
                yield "<div>I couldn't process that request properly.</div>"

        except Exception as e:
            logger.error(f'Agent error: {e}')
            yield f"<div>I'm having trouble processing that. Could you try rephrasing your request?</div>"
        
        yield "</span></div><script>document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;</script>"
    
    return StreamingHttpResponse(generate(), content_type='text/html')


@login_required
def trips_list(request):
    trips = Trip.objects.filter(user=request.user).exclude(status='archived')
    return render(request, 'trips.html', {'trips': trips})


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    version = trip.versions.order_by('-version_number').first()
    items = ItineraryItem.objects.filter(version=version).order_by('day_number', 'start_time') if version else ItineraryItem.objects.none()
    
    days = defaultdict(list)
    for item in items:
        days[item.day_number].append(item)
    days = dict(sorted(days.items()))
    
    # ── Per-day summaries ──────────────────────────────────────────────
    day_summaries = {}
    for day_num, day_items in days.items():
        day_cost = sum(item.cost_inr for item in day_items)
        if day_items:
            day_items[0].day_cost_sum = day_cost

        type_counts = defaultdict(int)
        for item in day_items:
            type_counts[item.place_type] += 1

        day_summaries[day_num] = {
            'total_cost': day_cost,
            'total_items': len(day_items),
            'attractions': type_counts.get('attraction', 0),
            'food': type_counts.get('food', 0),
            'hotel': type_counts.get('hotel', 0),
            'transit': type_counts.get('transit', 0),
            'activity': type_counts.get('activity', 0),
        }

    # ── Day narratives (AI-style story intros) ─────────────────────────
    day_narratives = {}
    time_greetings = {
        'morning': '🌅 Good morning!',
        'afternoon': '☀️ Good afternoon!',
        'evening': '🌆 Good evening!',
    }
    for day_num, day_items in days.items():
        if not day_items:
            continue
        first = day_items[0]
        greeting = time_greetings.get(first.time_period, '🌅 Good morning!')

        # Collect non-transit activity names for the narrative
        highlights = [
            it.place_name for it in day_items
            if it.place_type != 'transit'
        ][:4]

        if len(highlights) >= 3:
            narrative = (
                f"{greeting} Today you'll explore {highlights[0]}, "
                f"enjoy {highlights[1]}, and discover {highlights[2]}. "
                f"A perfect day awaits in {trip.destination}!"
            )
        elif len(highlights) == 2:
            narrative = (
                f"{greeting} Today features {highlights[0]} "
                f"followed by {highlights[1]} — "
                f"an unforgettable day in {trip.destination}!"
            )
        elif highlights:
            narrative = (
                f"{greeting} Today's highlight is {highlights[0]} "
                f"in beautiful {trip.destination}!"
            )
        else:
            narrative = f"{greeting} A relaxing travel day in {trip.destination}."

        day_narratives[day_num] = narrative

    # ── Trip-level stats for the hero ──────────────────────────────────
    trip_stats = {
        'total_items': items.count(),
        'total_activities': items.exclude(place_type='transit').count(),
        'total_cost': sum(item.cost_inr for item in items),
        'total_days': len(days),
        'food_count': items.filter(place_type='food').count(),
        'attraction_count': items.filter(place_type='attraction').count(),
    }
    
    from agent.tools import get_weather
    weather = get_weather(trip.destination, str(trip.start_date or ''))
    
    is_paid = hasattr(trip, 'payment') and trip.payment.status == 'paid'
    
    # Fetch hero + gallery images
    img_svc = ImageRetrievalService()
    try:
        hero_image = img_svc.get_hero_image(trip.destination, trip.category)
    except Exception:
        hero_image = {'url': trip.cover_image_url, 'provider': 'Pollinations'}
    
    try:
        gallery_images = img_svc.get_gallery_images(trip.destination, trip.category, limit=5)
    except Exception:
        gallery_images = []
    
    # Fetch destination knowledge hub
    from services.destination_info import DestinationInfoService
    try:
        dest_info = DestinationInfoService().get_info(trip.destination, trip.category)
    except Exception:
        dest_info = {}
    
    return render(request, 'itinerary.html', {
        'trip': trip,
        'days': days,
        'day_summaries': day_summaries,
        'day_narratives': day_narratives,
        'trip_stats': trip_stats,
        'weather': weather,
        'is_paid': is_paid,
        'hero_image': hero_image,
        'gallery_images': gallery_images,
        'dest_info': dest_info,
    })

from django.http import JsonResponse

@login_required
def trip_transport_api(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    
    from services.transport import TransportService
    from services.hotel import HotelProvider
    
    transport_svc = TransportService()
    try:
        transport_recommendations = transport_svc.get_recommendations(trip)
    except Exception as e:
        print(f"Transport API Error: {e}")
        transport_recommendations = {'error': str(e)}
        
    hotel_provider = HotelProvider()
    try:
        hotels = hotel_provider.get_hotels(trip)
    except Exception as e:
        print(f"Hotel API Error: {e}")
        hotels = []
        
    return JsonResponse({
        'transport': transport_recommendations,
        'hotels': hotels
    })


@login_required
def trip_pdf(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    
    is_paid = hasattr(trip, 'payment') and trip.payment.status == 'paid'
    if not is_paid:
        messages.warning(request, 'Please unlock the PDF by paying ₹99 first.')
        return redirect('trip_detail', pk=pk)
    
    version = trip.versions.order_by('-version_number').first()
    items = ItineraryItem.objects.filter(version=version).order_by('day_number', 'start_time') if version else ItineraryItem.objects.none()
    days = defaultdict(list)
    for item in items:
        days[item.day_number].append(item)
    days = dict(sorted(days.items()))
    
    for day_num, day_items in days.items():
        if day_items:
            day_items[0].day_cost_sum = sum(item.cost_inr for item in day_items)
    
    from services.pdf import generate_trip_pdf
    file_path = generate_trip_pdf(trip, days)

    # Serve as text file when mock PDF mode produces a .txt
    if file_path.endswith('.txt'):
        return FileResponse(
            open(file_path, 'rb'),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename=f'{trip.destination}_itinerary.txt',
        )

    return FileResponse(
        open(file_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=f'{trip.destination}_itinerary.pdf',
    )


@login_required
@require_POST
def trip_email(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    
    version = trip.versions.order_by('-version_number').first()
    items = ItineraryItem.objects.filter(version=version).order_by('day_number', 'start_time') if version else ItineraryItem.objects.none()
    days = defaultdict(list)
    for item in items:
        days[item.day_number].append(item)
    days = dict(sorted(days.items()))
    
    for day_num, day_items in days.items():
        if day_items:
            day_items[0].day_cost_sum = sum(item.cost_inr for item in day_items)
    
    from services.pdf import generate_trip_pdf
    from services.email_svc import send_itinerary_email, MOCK_MODE as EMAIL_MOCK_MODE
    
    pdf_path = generate_trip_pdf(trip, days)
    success = send_itinerary_email(request.user.email, trip, pdf_path)
    
    if success:
        if EMAIL_MOCK_MODE:
            messages.success(request, 'Email saved locally (demo mode) ✈️')
        else:
            messages.success(request, 'Itinerary sent to your email! ✈️')
    else:
        messages.error(request, 'Failed to send email. Please try again.')
    
    return redirect('trip_detail', pk=pk)


@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    trip.status = 'archived'
    trip.save()
    messages.success(request, f'{trip.destination} trip archived successfully.')
    return redirect('trips')


@login_required
@require_POST
def pay_create(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    
    from services.payment import create_order
    order = create_order(99)
    
    Payment.objects.update_or_create(
        trip=trip,
        defaults={
            'user': request.user,
            'razorpay_order_id': order['id'],
            'amount_paise': 9900,
            'status': 'pending',
        }
    )
    
    is_mock = order['id'].startswith('mock_')
    
    return JsonResponse({
        'order_id': order['id'],
        'amount': 9900,
        'key': os.environ.get('RAZORPAY_KEY_ID', ''),
        'name': request.user.get_full_name() or request.user.email,
        'email': request.user.email,
        'trip_id': str(pk),
        'mock_mode': is_mock,
    })


@login_required
@require_POST
def pay_verify(request):
    """Verify Razorpay payment signature."""
    try:
        data = json.loads(request.body)
        order_id = data['razorpay_order_id']
        payment_id = data['razorpay_payment_id']
        signature = data['razorpay_signature']
        trip_id = data['trip_id']
        
        # Auto-approve mock orders
        if order_id.startswith('mock_order_'):
            payment = Payment.objects.get(razorpay_order_id=order_id)
            payment.status = 'paid'
            payment.razorpay_payment_id = payment_id
            payment.paid_at = timezone.now()
            payment.save()

            payment.trip.status = 'paid'
            payment.trip.save()

            logger.info(f'[pay] Mock payment auto-approved for order {order_id}')
            return JsonResponse({'success': True, 'redirect': f'/trips/{trip_id}/'})
        
        from services.payment import verify_signature
        if verify_signature(order_id, payment_id, signature):
            payment = Payment.objects.get(razorpay_order_id=order_id)
            payment.status = 'paid'
            payment.razorpay_payment_id = payment_id
            payment.paid_at = timezone.now()
            payment.save()
            
            payment.trip.status = 'paid'
            payment.trip.save()
            
            return JsonResponse({'success': True, 'redirect': f'/trips/{trip_id}/'})
        else:
            return JsonResponse({'success': False}, status=400)
    except Exception as e:
        logger.error(f'Payment verify error: {e}')
        return JsonResponse({'success': False}, status=400)


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)

def item_image_api(request, pk):
    """API endpoint to dynamically fetch the best contextual image for an itinerary item."""
    item = get_object_or_404(ItineraryItem, pk=pk)
    
    visual_meta = item.visual_metadata
    if not visual_meta:
        # Fallback if the agent didn't populate it (e.g., old items or mock mode)
        visual_meta = {
            "primary_query": f"{item.place_name} in {item.version.trip.destination}",
            "city": item.version.trip.destination
        }
        
    engine = ImageRetrievalService()
    try:
        best_image = engine.get_image(visual_meta)
        return JsonResponse(best_image)
    except Exception as e:
        logger.error(f"Error fetching image for item {item.id}: {e}")
        return JsonResponse({"error": str(e)}, status=500)
