import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from ..models import Event, Photo, SubEvent, Subscription
from .payments.check_subscription import check_subscription
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

@login_required
def upload_complete(request, event_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    event = get_object_or_404(Event, event_id=event_id)

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

        # ✅ Subscription check (1 file at a time now)
        if not check_subscription(request, event, 1):
            return JsonResponse({
                "message": "Subscription limit reached",
                "redirect": "/billing/"
            }, status=403)

        with transaction.atomic():

            photo = Photo.objects.create(
                event=event,
                image=file_key,
                subevent=session
            )

            # update count
            Subscription.objects.filter(
                photographer=request.user,
                subscription_type="FREE"
            ).update(photo_count=F("photo_count") + 1)

        return JsonResponse({
            "success": True,
            "photo_id": photo.id
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Upload complete failed")

        return JsonResponse({"error": "Failed to save"}, status=500)