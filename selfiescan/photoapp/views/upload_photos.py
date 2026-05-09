from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden
from ..models import Event,Subscription
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

@login_required
def upload_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if event.photographer != request.user:
        return HttpResponseForbidden("You don't have access to this event.")

    sub = Subscription.objects.filter(photographer=request.user).first()

    is_unlimited_upload = False
    upload_limit = 100
    subscription_status = "none"   # "active" | "expired" | "free" | "none"
    if sub:
        if sub.subscription_type in ["MONTHLY", "YEARLY"]:
            if sub.end_date and sub.end_date >= timezone.now():
                is_unlimited_upload = True
                upload_limit = None
                subscription_status = "active"
            else:
                subscription_status = "expired"
        elif sub.subscription_type == "FREE":
            upload_limit = 100
            subscription_status = "free"
        else:
           subscription_status = "none"

    context = {
        "event": event,
        "is_unlimited_upload": is_unlimited_upload,
        "upload_limit": upload_limit,
        "total_photographers_upload": sub.photo_count if sub else 0,
        "billing_redirect_url": "/billing/",
        "subscription_status": subscription_status,  
    }

    return render(request, 'upload_photos.html', context)