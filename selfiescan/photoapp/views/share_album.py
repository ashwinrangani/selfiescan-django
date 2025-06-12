from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.paginator import Paginator
from ..models import Event, EventShare, Photo
import logging

logger = logging.getLogger(__name__)

def share_album(request, event_id):
    event = get_object_or_404(Event, event_id=event_id, photographer=request.user)
    
    # Check the 'view' query parameter to determine which photos to show
    view_mode = request.GET.get('view', 'all')  # Default to 'all'
    if view_mode == 'selected':
        photos_list = Photo.objects.filter(event=event, customer_selected=True).order_by('display_number')
    else:
        photos_list = Photo.objects.filter(event=event).order_by('display_number')
    
    customer_selected_photos = photos_list.filter(customer_selected=True).exists()
    number_of_selected_photos = photos_list.filter(customer_selected=True).count()
    
    # Log the number of photos
    logger.info(f"Event {event.id} has {photos_list.count()} photos in view mode '{view_mode}'")

    # Set up pagination - 12 photos per page
    paginator = Paginator(photos_list, 12)
    page = request.GET.get('page', 1)
    photos = paginator.get_page(page)

    # Check if a shareable link already exists
    event_share = EventShare.objects.filter(event=event, is_active=True).first()
    share_url = None
    if event_share:
        share_url = request.build_absolute_uri(reverse("customer_album_view", kwargs={"token": str(event_share.token)}))

    if request.method == "POST" and request.user.is_authenticated:
        try:
            # Check if the event is already shared
            event_share, created = EventShare.objects.get_or_create(
                event=event,
                defaults={"is_active": True}
            )

            # Generate the sharing URL
            share_url = request.build_absolute_uri(reverse("customer_album_view", kwargs={"token": str(event_share.token)}))
            logger.info(f"Generated shareable link for event {event.id}: {share_url}")

            return redirect(reverse("share_album", kwargs={"event_id": event_id}))

        except Event.DoesNotExist:
            return JsonResponse({"success": False, "error": "Event not found"}, status=404)
        except Exception as e:
            logger.error(f"Error in share_album: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return render(request, "share_album.html", {
        "event": event,
        "photos": photos,
        "share_url": share_url,
        "customer_selected_photos": customer_selected_photos,
        "number_of_selected_photos": number_of_selected_photos,
        "view_mode": view_mode  # Pass the current view mode to the template
    })