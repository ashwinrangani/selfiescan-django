from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ...models import Subscription, Payment
from django.utils import timezone


@login_required
def billing_dashboard(request):
    user = request.user
    subscription = Subscription.objects.get_or_create(photographer=user, defaults={'subscription_type': 'FREE'})[0]
        
    if subscription.subscription_type == 'FREE':
        current_cycle_start = None
        current_cycle_end = None
    else:
        current_cycle_start = subscription.start_date
        current_cycle_end = subscription.end_date
        
    context = {
        'subscription': subscription,
        'plans': [
            {'name': 'Free', 'price': '0', 'limit': '100 photos total', 'features': ['Basic upload', 'Face matching']},
            # {'name': 'Per Event', 'price': '₹350/event', 'limit': 'Unlimited per event', 'features': ['All free features']},
            {'name': 'Monthly', 'price': '₹800/month', 'limit': 'Unlimited events', 'features': ['All features', 'Portfolio', 'Analytics']},
            {'name': 'Yearly', 'price': '₹7000/year', 'limit': 'Unlimited events', 'features': ['All features', 'Portfolio', 'Analytics']},
        ],
        'current_cycle': {
            'start': current_cycle_start,
            'end': current_cycle_end,
            'remaining_photos': max(100 - subscription.photo_count, 0) if subscription.subscription_type == 'FREE' else 'Unlimited',
            'status': 'Active' if (subscription.subscription_type == 'YEARLY' or subscription.subscription_type =='MONTHLY' and subscription.end_date > timezone.now()) else 'Inactive',
            # 'status': 'Active' if (subscription.subscription_type == 'YEARLY' and subscription.end_date > timezone.now()) or EventSubscription.objects.filter(photographer=user, is_paid=True).exists() else 'Inactive',
        },
        'payments': Payment.objects.filter(photographer=user).order_by('-created_at')[:5],  # Last 5 payments
    }
    return render(request, 'subscription/billing.html', context)
 