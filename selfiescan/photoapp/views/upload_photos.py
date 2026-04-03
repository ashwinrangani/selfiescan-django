from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from ..models import Event, Photo, Subscription, SubEvent
#import razorpay
import logging
logger = logging.getLogger(__name__)
from .payments.check_subscription import check_subscription
from django.db import transaction
from django.db.models import F

#razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def upload_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if request.method == 'POST':
        session_id = request.POST.get("session_id")
        session = None

        if session_id:
            session = SubEvent.objects.filter(
                id=session_id,
                event=event
            ).first()
            
        upload_data = request.FILES.getlist('upload_data')

        if not check_subscription(request,event,len(upload_data)):
            return JsonResponse({
                "message": "Subscription limit reached, Please upgrade your plan.",
                "redirect": f"/billing/"
            }, status=403)

        if not upload_data:
            return JsonResponse({"message": "No photos uploaded"}, status=400)
        
                
        saved_data = []
        
        try:

            with transaction.atomic():
                
                for data in upload_data:
                    
                    photo = Photo(event=event, image=data, subevent=session)
                    photo.save()
                    saved_data.append(photo.image.name)
                      # all uploads fail → watch retry logic
            
                count = len(saved_data)
                
                Subscription.objects.filter(photographer=request.user,
                subscription_type="FREE"
                ).update(photo_count=F("photo_count") + count)
        
        except Exception as e:
            from django.core.files.storage import default_storage

            for s3_key in saved_data:
                default_storage.delete(s3_key)
            logger.exception("Upload failed")
            return JsonResponse({"message": "Upload failed"}, status=500)

        return JsonResponse({
            "upload_success": True,
            "uploaded_images": len(saved_data),
            "files": saved_data,
            "session_id": session.id if session else None,
        })
    
    return render(request, 'upload_photos.html', {"event": event})






