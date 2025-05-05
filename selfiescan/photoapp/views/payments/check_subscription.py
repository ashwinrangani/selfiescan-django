from ...models import Subscription
from django.utils import timezone

def check_subscription(request,event,new_photos_count):
    user = request.user
    subscription, created = Subscription.objects.get_or_create(photographer=user,defaults={'subscription_type':'FREE'})

    if subscription.subscription_type == "YEARLY" and subscription.end_date > timezone.now():
        return True
    if subscription.subscription_type == "MONTHLY" and subscription.end_date > timezone.now():
        return True
    # event_subscription = EventSubscription.objects.filter(event=event,photographer=user,is_paid=True).exists()

    # if event_subscription:
    #     return True

    if subscription.subscription_type == "FREE" and (subscription.photo_count + new_photos_count) <= 100:
        return True
    
    return False

