# photoapp/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from ..models import Event, Photo

def public_gallery(request, event_id, token):
    event = get_object_or_404(
        Event,
        event_id=event_id,
        public_token=token,
        is_public_gallery_enabled=True
    )

    # AJAX: Load More Photos
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 20))

        qs = Photo.objects.filter(event=event).order_by("id")
        photos = qs[offset: offset + limit]

        return JsonResponse({
            "photos": [{"id": p.id, "image_url": p.image.url} for p in photos],
            "loaded_photos": offset + len(photos),
            "total_photos": qs.count(),
        })

    # First Page Load
    photos = Photo.objects.filter(event=event).order_by("id")[:20]
    total_photos = Photo.objects.filter(event=event).count()
    studio_name = event.studio_name

    return render(request, "public_gallery.html", {
        "event": event,
        "event_id": event_id,
        "token": token,
        "photos": photos,
        "total_photos": total_photos,
        "studio_name": studio_name,
        "hide_navbar": True,
    })
    
    
