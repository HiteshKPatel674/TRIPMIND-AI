import uuid
from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    """Stores long-term user preferences for highly personalized AI generation."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Trip(models.Model):
    """A travel itinerary planned by a user."""

    CATEGORY_CHOICES = [
        ('beach', 'Beach'),
        ('adventure', 'Adventure'),
        ('family', 'Family'),
        ('honeymoon', 'Honeymoon'),
        ('food', 'Food'),
        ('spiritual', 'Spiritual'),
        ('general', 'General'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('complete', 'Complete'),
        ('paid', 'Paid'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    
    # Core inputs
    destination = models.CharField(max_length=200)
    
    # Canonical validated location
    destination_canonical = models.CharField(max_length=300, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    num_days = models.PositiveIntegerField(default=3)
    budget_inr = models.PositiveIntegerField(default=0)
    group_size = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    origin_city = models.CharField(max_length=100, blank=True)
    hotel_pref = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.destination} ({self.status})'

    @property
    def cover_image_url(self):
        """Generate a context-aware hero image URL for this destination."""
        from services.image_engine.providers import get_landmark_query
        import urllib.parse
        query = get_landmark_query(self.destination, self.category)
        prompt = (
            f"Ultra realistic cinematic travel photograph of {query}, "
            f"golden hour lighting, professional DSLR, "
            f"National Geographic style, vibrant colors, 8k"
        )
        encoded = urllib.parse.quote(prompt)
        return f"https://image.pollinations.ai/prompt/{encoded}?width=1600&height=900&nologo=true"

    @property
    def active_version(self):
        return self.versions.order_by('-version_number').first()


class TripVersion(models.Model):
    """A specific version of an itinerary to allow 'undo' and side-by-side comparison."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    overall_confidence = models.JSONField(default=dict, blank=True)
    
    # Complete JSON dump of the itinerary for this version
    itinerary_json = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ('trip', 'version_number')

    def __str__(self):
        return f'{self.trip.destination} - v{self.version_number}'

    @property
    def total_estimated_cost(self):
        return self.items.aggregate(total=models.Sum('cost_inr'))['total'] or 0

    @property
    def budget_used_pct(self):
        if self.trip.budget_inr:
            return min(int(self.total_estimated_cost / self.trip.budget_inr * 100), 100)
        return 0

    @property
    def total_activities(self):
        return self.items.exclude(place_type='transit').count()


class ItineraryItem(models.Model):
    """A single slot in a day's itinerary, attached to a specific TripVersion."""

    PLACE_TYPE_CHOICES = [
        ('attraction', 'Attraction'),
        ('food', 'Food'),
        ('hotel', 'Hotel'),
        ('transit', 'Transit'),
        ('activity', 'Activity'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(TripVersion, on_delete=models.CASCADE, related_name='items')
    
    day_number = models.PositiveIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    place_name = models.CharField(max_length=300)
    place_type = models.CharField(max_length=20, choices=PLACE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    cost_inr = models.PositiveIntegerField(default=0)
    maps_url = models.URLField(blank=True)
    rating = models.FloatField(null=True, blank=True)
    
    visual_metadata = models.JSONField(null=True, blank=True)
    
    # Confidence metrics: {"confidence": 0.94, "verified": true, "source": "Amadeus"}
    confidence_score = models.JSONField(default=dict, blank=True)
    
    # Alternative options calculated by the Scoring Engine
    alternatives = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['day_number', 'start_time']

    def __str__(self):
        return f'Day {self.day_number} – {self.place_name}'

    @property
    def contextual_image_url(self):
        return ""

    @property
    def category_icon(self):
        name_lower = self.place_name.lower()
        if self.place_type == 'transit':
            if 'flight' in name_lower or 'airport' in name_lower: return 'bi-airplane'
            if 'train' in name_lower or 'railway' in name_lower: return 'bi-train-front'
            if 'bus' in name_lower: return 'bi-bus-front'
            if 'walk' in name_lower: return 'bi-person-walking'
            if 'boat' in name_lower or 'ferry' in name_lower: return 'bi-water'
            if 'cab' in name_lower or 'taxi' in name_lower or 'uber' in name_lower: return 'bi-taxi-front'
            return 'bi-car-front'
        elif self.place_type == 'food':
            if 'breakfast' in name_lower: return 'bi-cup-hot'
            if 'dinner' in name_lower: return 'bi-moon-stars'
            if 'cafe' in name_lower or 'coffee' in name_lower: return 'bi-cup-straw'
            return 'bi-egg-fried'
        elif self.place_type == 'hotel':
            if 'check' in name_lower: return 'bi-door-open'
            return 'bi-building'
        elif self.place_type == 'activity':
            if any(w in name_lower for w in ['trek', 'hike', 'climb']): return 'bi-signpost-split'
            if any(w in name_lower for w in ['swim', 'beach', 'water', 'lake', 'river']): return 'bi-water'
            if any(w in name_lower for w in ['shop', 'market', 'mall', 'bazaar']): return 'bi-bag'
            if any(w in name_lower for w in ['spa', 'yoga', 'relax']): return 'bi-heart-pulse'
            return 'bi-lightning'
        else:
            if any(w in name_lower for w in ['temple', 'church', 'mosque', 'gurudwara']): return 'bi-buildings'
            if any(w in name_lower for w in ['museum', 'gallery', 'art']): return 'bi-bank'
            if any(w in name_lower for w in ['park', 'garden', 'forest', 'nature']): return 'bi-tree'
            if any(w in name_lower for w in ['fort', 'palace', 'castle', 'monument']): return 'bi-shield'
            if any(w in name_lower for w in ['lake', 'river', 'waterfall', 'dam']): return 'bi-water'
            if any(w in name_lower for w in ['sunset', 'sunrise', 'viewpoint', 'view']): return 'bi-sunrise'
            return 'bi-camera'

    @property
    def category_color(self):
        colors = {
            'attraction': '217, 91%, 60%',
            'food': '38, 92%, 50%',
            'hotel': '270, 67%, 60%',
            'transit': '200, 40%, 55%',
            'activity': '160, 84%, 39%',
        }
        return colors.get(self.place_type, '217, 91%, 60%')

    @property
    def category_label(self):
        name_lower = self.place_name.lower()
        if self.place_type == 'food':
            if 'breakfast' in name_lower: return 'Breakfast'
            if 'lunch' in name_lower: return 'Lunch'
            if 'dinner' in name_lower: return 'Dinner'
            if 'cafe' in name_lower or 'coffee' in name_lower: return 'Café'
            if 'street' in name_lower: return 'Street Food'
            return 'Dining'
        elif self.place_type == 'transit':
            if 'flight' in name_lower or 'airport' in name_lower: return 'Flight'
            if 'train' in name_lower: return 'Train'
            if 'walk' in name_lower: return 'Walking'
            if 'cab' in name_lower or 'taxi' in name_lower or 'uber' in name_lower: return 'Cab Ride'
            return 'Transit'
        elif self.place_type == 'hotel':
            return 'Stay'
        elif self.place_type == 'activity':
            if any(w in name_lower for w in ['shop', 'market', 'mall', 'bazaar']): return 'Shopping'
            if any(w in name_lower for w in ['trek', 'hike']): return 'Adventure'
            if any(w in name_lower for w in ['spa', 'yoga']): return 'Wellness'
            return 'Activity'
        else:
            if any(w in name_lower for w in ['temple', 'church', 'mosque']): return 'Heritage'
            if any(w in name_lower for w in ['museum', 'gallery']): return 'Museum'
            if any(w in name_lower for w in ['park', 'garden', 'nature']): return 'Nature'
            if any(w in name_lower for w in ['lake', 'river', 'waterfall']): return 'Waterfront'
            return 'Sightseeing'

    @property
    def time_period(self):
        hour = self.start_time.hour
        if hour < 12: return 'morning'
        if hour < 17: return 'afternoon'
        if hour < 20: return 'evening'
        return 'night'

    @property
    def duration_display(self):
        from datetime import datetime, timedelta
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        diff = end_dt - start_dt
        total_minutes = int(diff.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours and minutes: return f'{hours}h {minutes}m'
        elif hours: return f'{hours}h'
        return f'{minutes}m'

    @property
    def ai_tip(self):
        name_lower = self.place_name.lower()
        hour = self.start_time.hour
        tips = []

        if self.place_type == 'attraction':
            if hour < 10: tips.append('Visiting early means fewer crowds and better photos.')
            elif hour >= 14 and hour < 17: tips.append('Afternoon visits can be hot — carry water and sunscreen.')
            if not tips: tips.append('Ask locals for hidden gems nearby — they know best!')
        elif self.place_type == 'food':
            if 'dinner' in name_lower: tips.append('Book a window seat for the best ambiance.')
            else: tips.append('Ask the server for the chef\'s special recommendation.')
        elif self.place_type == 'hotel':
            if 'check' in name_lower and 'in' in name_lower: tips.append('Request a room with a view if available — often free!')
            else: tips.append('Explore the hotel amenities — you\'re paying for them!')
        elif self.place_type == 'transit':
            if 'train' in name_lower: tips.append('Window seats offer stunning views of the countryside.')
            else: tips.append('Enjoy the scenic route — the journey is part of the trip!')
        else:
            tips.append('Keep your camera ready — you won\'t want to miss this!')

        return tips[0] if tips else 'Enjoy every moment of this experience!'


class ChatSession(models.Model):
    """Stores the conversation history for a user session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    trip = models.ForeignKey(Trip, null=True, blank=True, on_delete=models.SET_NULL)
    messages = models.JSONField(default=list)
    graph_state = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Session {self.id} – {self.user.username}'


class Payment(models.Model):
    """Razorpay payment record linked to a trip."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    amount_paise = models.PositiveIntegerField(default=9900)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DestinationImageCache(models.Model):
    """Enhanced cache for contextual images retrieved from external APIs."""
    query_hash = models.CharField(max_length=64, unique=True, db_index=True)
    query = models.CharField(max_length=500)
    provider = models.CharField(max_length=50)
    image_url = models.URLField(max_length=1000)
    thumbnail_url = models.URLField(max_length=1000, blank=True)
    attribution_text = models.CharField(max_length=500, blank=True)
    attribution_url = models.URLField(max_length=1000, blank=True)
    
    # Context
    destination_id = models.CharField(max_length=100, blank=True)
    license = models.CharField(max_length=100, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.provider} - {self.query[:30]}'


class CostLog(models.Model):
    """Tracks LLM token costs and API costs per trip."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='cost_logs')
    llm_cost_usd = models.FloatField(default=0.0)
    api_cost_usd = models.FloatField(default=0.0)
    provider_breakdown = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'CostLog for {self.trip.destination}'
