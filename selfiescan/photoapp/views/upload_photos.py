from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from ..models import Event, Photo, Subscription
import razorpay
import logging
logger = logging.getLogger(__name__)
from .payments.check_subscription import check_subscription

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def upload_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if request.method == 'POST':
        
        upload_data = request.FILES.getlist('upload_data')

        if not check_subscription(request,event,len(upload_data)):
            return JsonResponse({
                "message": "Subscription limit reached, Please upgrade your plan.",
                "redirect": f"/billing/"
            }, status=403)

        if not upload_data:
            return JsonResponse({"message": "No photos uploaded"}, status=400)

        saved_data = []
        for data in upload_data:
            photo = Photo(event=event, image=data)
            photo.save()  # `post_save` will trigger Celery task
            saved_data.append(photo.image.url)
        
        subscription = Subscription.objects.get(photographer=request.user)
        if subscription.subscription_type == 'FREE':
            subscription.photo_count += 1
            subscription.save()

        return JsonResponse({
            "upload_success": True,
            "uploaded_images": len(saved_data),
            "files": saved_data
        })
    
    return render(request, 'upload_photos.html', {"event": event})






