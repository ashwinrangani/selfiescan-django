from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from ...models import Payment
import logging
import razorpay

logger = logging.getLogger(__name__)

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def subscribe(request, event_id=None):  # event_id is now optional
    if request.method == 'POST':
        plan = request.POST.get('plan')  # 'per_event' or 'yearly'

        # if plan == 'per_event':
        #     if not event_id:
        #         return JsonResponse({"message": "Event ID required for per event subscription."}, status=400)
        #     event = get_object_or_404(Event, event_id=event_id)
        #     amount = 35000  # Rs 350
        #     payment_type = 'PER_EVENT'
        if plan == 'Monthly':
            amount = 80000
            payment_type = 'MONTHLY'
        elif plan == 'Yearly':
            event = None
            amount = 700000  # Rs 7000
            payment_type = 'YEARLY'
        else:
            return JsonResponse({"message": "Invalid plan selected."}, status=400)

        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {}
        }

        # Add event_id in notes only for per_event payments
        # if event:
        #     order_data['notes']['event_id'] = str(event.id)
        order = razorpay_client.order.create(data=order_data)

        Payment.objects.create(
            photographer=request.user,
            amount=amount / 100,
            payment_type=payment_type,
            order_id=order['id']
        )

        return render(request, 'subscription/payment.html', {
            'order_id': order['id'],
            'amount': amount / 100,
            'key_id': settings.RAZORPAY_KEY_ID,
            # 'event_id': event_id,
            'plan': plan
        })

    # if event_id:
    #     event = get_object_or_404(Event, event_id=event_id)
    # else:
    #     event = None

    # return render(request, 'subscription/subscribe.html', {'event': event})
    return redirect('billing_dashboard')