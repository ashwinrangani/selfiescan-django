from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from ..models import Event

@login_required
@require_POST
def toggle_public_gallery(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    # Only photographer can update
    if event.photographer != request.user:
        return JsonResponse({"error": "Not allowed"}, status=403)

    enabled = request.POST.get("enabled") == "true"
    event.is_public_gallery_enabled = enabled
    event.save()

    public_url = ""
    if enabled:
        public_url = request.build_absolute_uri(
            reverse("public_gallery", args=[event.event_id, event.public_token])
        )

    return JsonResponse({
        "enabled": enabled,
        "public_url": public_url,
    })
    
@require_POST
def update_studio_name(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    studio_name = request.POST.get("studio_name", "").strip()

    event.studio_name = studio_name
    event.save(update_fields=["studio_name"])

    return JsonResponse({
        "success": True,
        "studio_name": studio_name,
    })
