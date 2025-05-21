from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from ..models import Event, EventShare, Photo
from django.http import HttpResponseForbidden
import logging
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def customer_album_view(request, token):
    event_share = get_object_or_404(EventShare, token=token, is_active=True)
    event = event_share.event
    all_photos = Photo.objects.filter(event=event).order_by('display_number')
    total_photos = all_photos.count()  # Get total photo count

    if request.method == "POST":
        selected_photo_ids = request.POST.getlist("selected_photos")
        all_photos.update(customer_selected=False)
        Photo.objects.filter(id__in=selected_photo_ids, event=event).update(customer_selected=True)
        # Removed messages.success; notification will be handled client-side
        return redirect(reverse("customer_album_view", kwargs={"token": token}))

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 20))
        paginated_photos = all_photos[offset:offset + limit]
        data = [{
            "id": p.id,
            "display_number": p.display_number if p.display_number is not None else "",  # Handle None as empty string
            "image_url": p.image.url,
            "selected": p.customer_selected
        } for p in paginated_photos]
        return JsonResponse({
            "photos": data,
            "total_photos": total_photos,  
            "loaded_photos": offset + len(paginated_photos)  # Number of photos loaded so far
        })

    return render(request, 'customer_album.html', {
        'event': event,
        'photos': all_photos[:20],
        'total_photos': total_photos,  
        "hide_navbar": True, # conditional rendering of navbar implemented in base.html
    })