import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from ..models import Event, Photo, SubEvent, Subscription
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

@login_required
def upload_complete(request, event_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    event = get_object_or_404(Event, event_id=event_id)
    
    if event.photographer != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        data = json.loads(request.body)
        file_key = data.get("file_key")
        session_id = data.get("session_id")

        if not file_key:
            return JsonResponse({"error": "Missing file_key"}, status=400)

        session = None
        if session_id:
            session = SubEvent.objects.filter(
                id=session_id,
                event=event
            ).first()

        from django.utils import timezone

        with transaction.atomic():

            sub = Subscription.objects.select_for_update().filter(
                photographer=request.user
            ).first()

            # --- VALIDATION ---
            if sub:
                if sub.subscription_type == "FREE":
                    if sub.photo_count >= 100:
                        return JsonResponse({
                            "message": "Subscription limit reached",
                            "redirect": "/billing/"
                        }, status=403)

                elif sub.subscription_type in ["MONTHLY", "YEARLY"]:
                    if not sub.end_date or sub.end_date < timezone.now():
                        return JsonResponse({
                            "message": "Subscription expired",
                            "redirect": "/billing/"
                        }, status=403)

            else:
                return JsonResponse({
                    "message": "No subscription found",
                    "redirect": "/billing/"
                }, status=403)

            # --- CREATE PHOTO ---
            photo = Photo.objects.create(
                event=event,
                image=file_key,
                subevent=session
            )

            # --- UPDATE COUNT ---
            if sub.subscription_type == "FREE":
                sub.photo_count += 1
                sub.save(update_fields=["photo_count"])
        
        logger.info(f"""
                User: {request.user}
                Type: {sub.subscription_type}
                End date: {sub.end_date}
                Now: {timezone.now()}
                Photo count: {sub.photo_count}
                """)
        return JsonResponse({
            "success": True,
            "photo_id": photo.id
        })
    except Exception as e:
       
        logger.exception("Upload complete failed")

        return JsonResponse({"error": "Failed to save"}, status=500)