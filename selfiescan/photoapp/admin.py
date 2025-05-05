from django.contrib import admin
from .models import Event, Subscription, Payment

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'photographer', 'date', 'event_id','branding_enabled')
    list_filter = ('photographer', 'date')
    search_fields = ('name', 'photographer__username')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('photographer', 'subscription_type', 'end_date', 'unsubscribed', 'last_notified')
    list_filter = ('subscription_type', 'unsubscribed')
    search_fields = ('photographer__username',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('photographer', 'amount', 'payment_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('photographer__username', 'payment_id')
