from django.shortcuts import redirect, get_object_or_404
from ..models import Event, Photo, Subscription
from django.http import JsonResponse
import json


def delete_selected_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if request.method == "POST":
        data = json.loads(request.body)
        photo_ids = data.get("photo_ids", [])

        if not photo_ids:
            messages.warning(request, "No photos selected for deletion.")
            return JsonResponse({"message": "No photos selected."}, status=400)

        photos = Photo.objects.filter(event=event, id__in=photo_ids)
        deleted_count = photos.count()

        # Delete files (image + branded image if exists)
        for photo in photos:
            if photo.image:
                photo.image.delete(save=False)
            if photo.branded_image:
                photo.branded_image.delete(save=False)

        # Adjust subscription
        try:
            subscription = Subscription.objects.get(photographer=request.user)
            subscription.photo_count = max(subscription.photo_count - deleted_count, 0)
            subscription.save()
        except ObjectDoesNotExist:
            pass  # skip if no subscription (e.g. admin delete)

        # Finally, delete DB entries
        photos.delete()

        return JsonResponse({"success": True, "message": f"{deleted_count} photos deleted successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request."})