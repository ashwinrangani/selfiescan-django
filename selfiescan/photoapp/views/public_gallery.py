from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from ..models import Event, Photo, SubEvent
from photoapp.utils.s3_download import generate_presigned_download

def public_gallery(request, event_id, token):
    event = get_object_or_404(
        Event,
        event_id=event_id,
        public_token=token,
        is_public_gallery_enabled=True
    )
    session_id = request.GET.get("session")
    base_qs = (
        Photo.objects
        .filter(event=event)
        .only("id", "image", "thumb_image", "medium_image", "large_image", "event")
        .order_by("image")
    )
    # Filter by session if provided
    if session_id:
        base_qs = base_qs.filter(subevent_id=session_id)
    # AJAX: Load More
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 24))

        photos = base_qs[offset: offset + limit]

        return JsonResponse({
            "photos": [
                {
                    "id": p.id,
                    "thumb": p.thumb_image.url if p.thumb_image else p.image.url,
                    "medium": p.medium_image.url if p.medium_image else p.image.url,
                    "large": generate_presigned_download(p.large_image if p.large_image else p.image),
                }
                for p in photos
            ],
            "loaded_photos": offset + len(photos),
            "total_photos": base_qs.count(),
        })

    # First Page Load
    photos = base_qs[:24]
    total_photos = base_qs.count()

    photo_data = [
        {
            "obj": p,
            "download_url": generate_presigned_download(p.large_image if p.large_image else p.image)
            if event.is_public_gallery_downloadable else None
        }
        for p in photos
    ]

    return render(request, "public_gallery.html", {
        "event": event,
        "event_id": event_id,
        "token": token,
        "photos": photo_data if photo_data else None,
        "total_photos": total_photos,
        "studio_name": event.studio_name,
        "hide_navbar": True,
        "sessions": event.subevents.all(),
        "active_session": session_id,
    })

