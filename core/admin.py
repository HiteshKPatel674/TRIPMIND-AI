from django.contrib import admin
from .models import ChatSession, ItineraryItem, Payment, Trip, UserProfile, TripVersion, CostLog, DestinationImageCache

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('destination', 'status', 'category', 'user', 'created_at')

@admin.register(TripVersion)
class TripVersionAdmin(admin.ModelAdmin):
    list_display = ('trip', 'version_number', 'created_at')

@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = ('place_name', 'version', 'day_number', 'place_type', 'cost_inr')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'created_at', 'updated_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('trip', 'status', 'amount_paise', 'paid_at')

@admin.register(DestinationImageCache)
class DestinationImageCacheAdmin(admin.ModelAdmin):
    list_display = ('query', 'provider', 'timestamp')

@admin.register(CostLog)
class CostLogAdmin(admin.ModelAdmin):
    list_display = ('trip', 'llm_cost_usd', 'api_cost_usd', 'created_at')
