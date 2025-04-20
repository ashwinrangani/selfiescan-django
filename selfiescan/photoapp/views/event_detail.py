import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from ..models import Event, Photo
from django.contrib import messages
from django.core.paginator import Paginator,PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.template.loader import render_to_string

def event_detail(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)
    
    old_folder_name = event.name
    # Handle event updates (POST)
    if request.method == "POST":
        new_name = request.POST.get("name", event.name)
        new_date = request.POST.get("date", event.date)

        new_location = request.POST.get("location", event.location)

        # Check if the event name is unique
        if event.name != new_name and Event.objects.filter(photographer=event.photographer, name=new_name).exclude(event_id=event.event_id).exists():
            messages.error(request, "An event with this name already exists. Please choose a different name.")
        else:
            event.name = new_name
            event.date = new_date
            event.location = new_location
            event.save()
            # rename the directory with updated event name
            if old_folder_name != new_name:
                rename_event_directory(event.photographer.username, old_folder_name, new_name)
            
            messages.success(request, "Event updated successfully!")
            return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))

    photos_list = Photo.objects.filter(event=event).order_by('-id')  # Adjust ordering as needed
    photos_count = photos_list.count()
    
    # Set up pagination - 12 photos
    paginator = Paginator(photos_list, 12)
    page = request.GET.get('page', 1)
    photos = paginator.get_page(page)
    
    return render(request, "event_detail.html", {
        "event": event, 
        "num_photos": photos_count,
        "photos": photos
    })

def rename_event_directory(photographer_username, old_name, new_name):
    base_dir = os.path.join(settings.MEDIA_ROOT, "photos", photographer_username)
    old_path = os.path.join(base_dir, old_name)
    new_path = os.path.join(base_dir, new_name)

    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f"Renamed {old_path} to {new_path}")
    else:
        print(f"old event folder does not exists")


def load_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)
    photos_list = Photo.objects.filter(event=event).order_by('-id')

    paginator = Paginator(photos_list, 12)
    page = request.GET.get('page', 1)

    try:
        photos = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        photos = paginator.page(1)

    # Render the photo grid and pagination controls separately
    html = render_to_string('partials/photo_grid.html', {
        'photos': photos,
        'event': event
    })

    pagination_html = render_to_string('partials/pagination_controls.html', {
        'photos': photos,
        'paginator': paginator
    })

    return JsonResponse({
        'html': html,
        'pagination_html': pagination_html
    })

def create_branding(request, event_id):
    if request.method == "POST":
        event = Event.objects.get(event_id=event_id, photographer=request.user)

        branding_enabled = request.POST.get("branding_enabled") in ["true", "on", "1"]
        branding_text = request.POST.get("branding_text", "").strip()
        branding_image = request.FILES.get('branding_image')

        if branding_enabled:
            event.branding_enabled = True

            # Always update branding_text, even if it's empty
            event.branding_text = branding_text
            
            # Update branding_image only if a new image is uploaded
            if branding_image:
                event.branding_image = branding_image

        else:
            # Branding is turned off, clear everything
            event.branding_enabled = False
            event.branding_text = ""
            event.branding_image = None

        event.save()

        return JsonResponse({
            "success": True,
            "logo_url": event.branding_image.url if event.branding_image else ""
        })

    return JsonResponse({"success": False}, status=400)

def remove_branding_logo(request, event_id):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            event = Event.objects.get(event_id=event_id, photographer=request.user)
            event.branding_image = None
            event.save()
            return JsonResponse({"success": True})
        except Event.DoesNotExist:
            return JsonResponse({"success": False, "error": "Event not found"}, status=404)

    return JsonResponse({"success": False}, status=400)