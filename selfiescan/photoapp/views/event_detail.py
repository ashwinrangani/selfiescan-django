import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from ..models import Event, Photo, Subscription
from django.contrib import messages
from django.core.paginator import Paginator,PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from ..tasks import branded_photo

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

    # total photos uploaded by photographer(all events)
    total_photographers_upload = Photo.objects.filter(event__photographer=request.user).count()
    subscription = Subscription.objects.filter(photographer=request.user).first()
    
    is_unlimited_upload = False
    if subscription and subscription.subscription_type in ["MONTHLY", "YEARLY"] and subscription.end_date > timezone.now():
        is_unlimited_upload = True
    
    return render(request, "event_detail.html", {
        "event": event, 
        "num_photos": photos_count,
        "photos": photos,
        "total_photographers_upload": total_photographers_upload,
        "is_unlimited_upload": is_unlimited_upload,
        "billing_redirect_url": "/billing/",
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
        try:
            event = Event.objects.get(event_id=event_id, photographer=request.user)
            branding_enabled = request.POST.get("branding_enabled") in ["true", "on", "1"]
            branding_type = request.POST.get("branding_type", "").strip()
            branding_text = request.POST.get("branding_text", "").strip()
            branding_image = request.FILES.get("branding_image")
            
            # if branding settings have changed or branding is being disabled
            branding_changed = (
                # Case 1: Branding is enabled and settings have changed
                (branding_enabled and (
                    event.branding_text != branding_text or
                    (branding_image is not None and event.branding_image != branding_image) or
                    (branding_type == "text" and event.branding_image) or
                    (branding_type == "logo" and event.branding_text)
                )) or
                # Case 2: Branding is being disabled (was enabled, now disabled)
                (event.branding_enabled and not branding_enabled)
            )

            if branding_changed:
                # Reset branding status and clear old branded images
                photos = Photo.objects.filter(event=event)
                for photo in photos:
                    if photo.branded_image:
                        photo.branded_image.delete(save=False)  # Delete from storage
                        photo.branded_image = None  # Explicitly clear the field
                    photo.is_branded = False
                    photo.save(update_fields=['branded_image', 'is_branded'])
                
            if branding_enabled and branding_type in ["logo", "text"]:
                event.branding_enabled = True
                if branding_type == "text" and branding_text:
                    event.branding_text = branding_text
                    event.branding_image = None  # Clear logo
                elif branding_type == "logo":
                    event.branding_text = ""  # Clear text
                    if branding_image:
                        event.branding_image = branding_image
                    # Note: If no branding_image is uploaded, keep existing branding_image (if any)
            else:
                # Branding disabled or invalid type, clear all branding fields
                event.branding_enabled = False
                event.branding_text = ""
                event.branding_image = None

            event.save()

            return JsonResponse({
                "success": True,
                "logo_url": event.branding_image.url if event.branding_image else "",
                "branding_text": event.branding_text
            })
        except Event.DoesNotExist:
            return JsonResponse({"success": False, "error": "Event not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)

def remove_branding_logo(request, event_id):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            event = Event.objects.get(event_id=event_id, photographer=request.user)
            event.branding_image = None
            event.save()
            return JsonResponse({
                "success": True,
                "branding_text": event.branding_text
                })
        except Event.DoesNotExist:
            return JsonResponse({"success": False, "error": "Event not found"}, status=404)

    return JsonResponse({"success": False}, status=400)


def start_branding(request, event_id):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            event = Event.objects.get(event_id=event_id, photographer=request.user)
            if not event.branding_enabled:
                return JsonResponse({"success": False, "message": "Branding is not enabled for this event."}, status=400)

            photos = Photo.objects.filter(event=event)
            if not photos.exists():
                return JsonResponse({"success": False, "message": "No photos to brand."}, status=400)

            unprocessed_photos = photos.filter(is_processed=False).count()
            if unprocessed_photos > 0:
                return JsonResponse({
                    "success": False,
                    "message": f"Cannot start branding: {unprocessed_photos} photos are still processing."
                }, status=400)

            # Trigger branding task for each photo
            for photo in photos:
                if not photo.is_branded:  # Skip already branded photos
                    branded_photo.delay(photo.id)
                
                

            return JsonResponse({"success": True, "message": "Branding started for event photos."}, status=200)

        except Event.DoesNotExist:
            return JsonResponse({"success": False, "error": "Event not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)