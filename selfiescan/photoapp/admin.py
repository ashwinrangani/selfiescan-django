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



from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect

from .models import Photo, Event
from .tasks import process_event_photos
from .utils.photo_processing_monitor import get_unprocessed_photo_groups


class PhotoProcessingAdmin(admin.ModelAdmin):
    change_list_template = "admin/photo_processing_monitor.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "rerun/<int:event_id>/",
                self.admin_site.admin_view(self.rerun_processing),
                name="rerun_processing",
            ),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        extra = extra_context or {}
        extra["groups"] = get_unprocessed_photo_groups()
        return super().changelist_view(request, extra)

    def rerun_processing(self, request, event_id):
        process_event_photos.delay(event_id)
        messages.success(request, "Processing re-triggered successfully!")
        return redirect("admin:photoapp_photo_changelist")


admin.site.register(Photo, PhotoProcessingAdmin)


