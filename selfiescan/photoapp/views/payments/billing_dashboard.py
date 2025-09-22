from django.shortcuts import render
from ...models import Subscription, Payment
from django.utils import timezone


def billing_dashboard(request):
    # Initialize defaults for unauthenticated users
    subscription = None
    current_cycle_start = None
    current_cycle_end = None
    remaining_photos = 0
    status = 'Inactive'
    payments = []

    if request.user.is_authenticated:
        user = request.user
        # Get or create subscription for authenticated users
        subscription = Subscription.objects.get_or_create(
            photographer=user,
            defaults={'subscription_type': 'FREE'}
        )[0]

        if subscription.subscription_type == 'FREE':
            current_cycle_start = None
            current_cycle_end = None
            remaining_photos = max(100 - subscription.photo_count, 0)
        else:
            current_cycle_start = subscription.start_date
            current_cycle_end = subscription.end_date
            remaining_photos = 'Unlimited'

        status = 'Active' if (
            subscription.subscription_type in ['YEARLY', 'MONTHLY'] and
            subscription.end_date > timezone.now()
        ) else 'Inactive'

        payments = Payment.objects.filter(photographer=user).order_by('-created_at')[:5]

    context = {
        'subscription': subscription,
        'plans': [
            {'name': 'Free', 'price': '0', 'limit': '100 photos total', 'features': ['Basic upload', 'Face matching']},
            {'name': 'Monthly', 'price': '₹800/month', 'limit': 'Unlimited events', 'features': ['All features', 'Portfolio', 'Analytics']},
            {'name': 'Yearly', 'price': '₹7000/year', 'limit': 'Unlimited events', 'features': ['All features', 'Portfolio', 'Analytics']},
        ],
        'current_cycle': {
            'start': current_cycle_start,
            'end': current_cycle_end,
            'remaining_photos': remaining_photos,
            'status': status,
        },
        'payments': payments,
    }

    return render(request, 'subscription/billing.html', context)
