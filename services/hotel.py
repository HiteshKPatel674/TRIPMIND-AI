import os
import requests
import datetime
import random
from core.models import Trip
from .mock_transport import get_mock_hotels

class HotelProvider:
    def get_hotels(self, trip: Trip) -> list:
        dest = trip.destination
        
        if trip.start_date:
            try:
                if isinstance(trip.start_date, str):
                    start_date = datetime.datetime.strptime(trip.start_date, '%Y-%m-%d').date()
                else:
                    start_date = trip.start_date
            except Exception:
                start_date = datetime.date.today() + datetime.timedelta(days=30)
        else:
            start_date = datetime.date.today() + datetime.timedelta(days=30)
            
        end_date = start_date + datetime.timedelta(days=trip.num_days)
        adults = trip.group_size
        rooms = max(1, (adults + 1) // 2)
        
        # Check for SERPAPI_KEY
        serpapi_key = os.environ.get('SERPAPI_KEY')
        if serpapi_key:
            return self._get_serpapi_hotels(trip, dest, start_date, end_date, adults, serpapi_key)
            
        hotels = get_mock_hotels(dest, start_date, end_date)
        for h in hotels:
            h['book_url'] = f"https://www.booking.com/searchresults.html?ss={dest}&checkin={start_date.strftime('%Y-%m-%d')}&checkout={end_date.strftime('%Y-%m-%d')}&group_adults={adults}&no_rooms={rooms}"
        return hotels[:15]
        
    def _get_serpapi_hotels(self, trip, dest, start_date, end_date, adults, api_key):
        query = dest
        if trip.hotel_pref:
            query = f"{trip.hotel_pref} in {dest}"
        else:
            query = f"Best hotels in {dest}"
            
        params = {
            "engine": "google_hotels",
            "q": query,
            "check_in_date": start_date.strftime('%Y-%m-%d'),
            "check_out_date": end_date.strftime('%Y-%m-%d'),
            "adults": adults,
            "currency": "INR",
            "api_key": api_key
        }
        
        try:
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = response.json()
            properties = data.get("properties", [])
            
            import urllib.parse
            
            reasons = [
                "Top choice from Google Hotels",
                "Great value for price",
                "Excellent traveler reviews",
                "Highly recommended",
                "Best rated in area",
            ]
            
            hotels = []
            for i, p in enumerate(properties):
                rate = p.get('rate_per_night', {}).get('lowest', 0)
                if not rate:
                    try:
                        rate_str = p.get('rate_per_night', {}).get('extracted_lowest', '0')
                        rate = int(''.join(filter(str.isdigit, str(rate_str))))
                    except Exception:
                        rate = random.randint(2000, 10000)
                
                name = p.get('name', 'Hotel')
                stars = p.get('hotel_class', random.randint(3, 5))
                
                # Use original image if available for better quality
                image_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote('Luxury hotel ' + name + ' in ' + dest)}?width=600&height=400&nologo=true"
                if p.get('images'):
                    image_url = p['images'][0].get('original_image', p['images'][0].get('thumbnail', image_url))
                
                hotel_search = urllib.parse.quote(f"{name} {dest}")
                book_url = (
                    f"https://www.booking.com/searchresults.html"
                    f"?ss={hotel_search}"
                    f"&checkin={start_date.strftime('%Y-%m-%d')}"
                    f"&checkout={end_date.strftime('%Y-%m-%d')}"
                    f"&group_adults={adults}&no_rooms=1"
                )
                
                maps_query = urllib.parse.quote(f"{name} {dest} India")
                maps_url = f"https://www.google.com/maps/search/{maps_query}"
                    
                hotels.append({
                    'id': f"SERP-{i}",
                    'name': name,
                    'stars': stars,
                    'price_per_night': rate,
                    'rating': p.get('overall_rating', 4.0),
                    'reviews': p.get('reviews', random.randint(50, 500)),
                    'amenities': p.get('amenities', [])[:4],
                    'image_placeholder': image_url,
                    'book_url': book_url,
                    'maps_url': maps_url,
                    'recommendation_reason': random.choice(reasons) if i < 3 else None,
                })
            
            # If nothing returned, fallback to mock
            if not hotels:
                raise Exception("Empty properties from SerpApi")
                
            return hotels
            
        except Exception as e:
            print(f"SerpApi Error: {e}")
            # Fallback to mock
            hotels = get_mock_hotels(dest, start_date, end_date)
            for h in hotels:
                h['book_url'] = f"https://www.booking.com/searchresults.html?ss={dest}&checkin={start_date.strftime('%Y-%m-%d')}&checkout={end_date.strftime('%Y-%m-%d')}&group_adults={adults}"
            return hotels[:15]
