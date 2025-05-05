from ..models import Subscription
from django.shortcuts import render
from django.utils import timezone

def homepage(request):
    subscription = None  # Default to None
    if request.user.is_authenticated:
        subscription, _ = Subscription.objects.get_or_create(
            photographer=request.user,
            defaults={'subscription_type': 'FREE'}
        )
    return render(request, 'homepage.html', {
        "subscription": subscription,
        "now": timezone.now(),
    })
