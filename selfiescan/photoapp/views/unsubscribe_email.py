from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from ..models import Subscription
from django.contrib.auth.models import User

def unsubscribe_reminders(request, user_id):
    user = get_object_or_404(User, id=user_id)
    Subscription.objects.filter(photographer=user).update(unsubscribed=True)
    messages.success(request, "You've been unsubscribed from subscription reminders.")
    return redirect("/")  # or your landing page
