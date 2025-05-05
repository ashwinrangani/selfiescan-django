from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from ...models import Subscription, Payment
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import razorpay
import json
import logging
from django.utils import timezone
logger = logging.getLogger(__name__)

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# for the local developent testing
@csrf_exempt
def payment_success(request):
    if request.method == "GET":
        payment_id = request.GET.get('payment_id')
        order_id = request.GET.get('order_id')

        if not payment_id or not order_id:
            logger.error("Missing payment id or order id in GET request")
            return HttpResponse("Missing payment_id or order_id", status=400)
        try:
            payment = Payment.objects.get(order_id=order_id)
            payment.payment_id = payment_id
            payment.status = "COMPLETED"
            payment.save()

            subscription = Subscription.objects.get(photographer=payment.photographer)
            if payment.payment_type == 'YEARLY':
                subscription.subscription_type = 'YEARLY'
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=365)
                subscription.save()
            elif payment.payment_type == 'MONTHLY':
                subscription.subscription_type = 'MONTHLY'
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=30)
                subscription.save()
            logger.info(f"Payment {payment_id} completed for {payment.photographer.username}")
            return render(request, 'subscription/payment_success.html', {
                'payment_id': payment_id,
                'order_id': order_id,
                'subscription_type': subscription.subscription_type,
            })
        
        except Payment.DoesNotExist:
            logger.error(f"Payment with order_id {order_id} not found")
            return HttpResponse('Payment not found', status=404)
        
        except Subscription.DoesNotExist:
            logger.error(f"Subscription for payment {payment_id} not found")
            return HttpResponse('Subscription not found', status=404)
        
        except Exception as e:
            logger.error(f"Error in payment success: {str(e)}")
            return HttpResponse(f'Failed to update: {str(e)}', status=500)
    
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = data['payload']['payment']['entity']['id']
            order_id = data['payload']['payment']['entity']['order_id']

            payment = Payment.objects.get(order_id=order_id)
            payment.payment_id = payment_id
            payment.status = "COMPLETED"
            payment.save()

            subscription = Subscription.objects.get(photographer=payment.photographer)

            if payment.payment_type == 'YEARLY':
                subscription.subscription_type = 'YEARLY'
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=365)
                subscription.save()
            elif payment.payment_type == 'MONTHLY':
                subscription.subscription_type = 'MONTHLY'
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=30)
                subscription.save()

            logger.info(f"Payment {payment_id} completed for {payment.photographer.username}")
            return HttpResponse('Payment updated successfully', status=200)

        except Exception as e:
            logger.error(f"Error in payment webhook: {str(e)}")
            return HttpResponse(f'Failed to update: {str(e)}', status=500)

    return HttpResponse('Invalid request method', status=405)

# for the production
@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        event = data.get('event')

        if event == 'payment.captured':
            payment_id = data['payload']['payment']['entity']['id']
            order_id = data['payload']['payment']['entity']['order_id']

            try:
                payment = Payment.objects.get(order_id=order_id)
                payment.payment_id = payment_id
                payment.status = 'COMPLETED'
                payment.save()

                subscription = Subscription.objects.get(photographer=payment.photographer)

                if payment.payment_type == 'YEARLY':
                    # Update subscription
                    subscription.subscription_type = 'YEARLY'
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timedelta(days=365)
                    subscription.save()
                # else:
                #     # Only if per event, create EventSubscription
                #     event_id = data['payload']['payment']['entity']['notes'].get('event_id')
                #     if event_id:
                #         EventSubscription.objects.create(
                #             event_id=event_id,
                #             photographer=payment.photographer,
                #             is_paid=True
                #         )
                if payment.payment_type == 'MONTHLY':
                    # Update subscription
                    subscription.subscription_type = 'MONTHLY'
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timedelta(days=30)
                    subscription.save()

                logger.info(f"Payment {payment_id} completed for {payment.photographer.username}")
            except Exception as e:
                logger.error(f"Error in payment webhook: {str(e)}")
                return HttpResponse(status=500)
        return HttpResponse(status=200)
    return HttpResponse(status=405)