from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from ..models import Event, Photo
import os

# delete event with all photos
def event_delete(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)
    
    if request.method == "POST":

        event_folder = os.path.join(settings.MEDIA_ROOT, "photos", event.photographer.username, event.name)
        photos = Photo.objects.filter(event=event)
        
        # Delete the image files from storage
        for photo in photos:
            if photo.image: 
                photo.image.delete(save=False)  # Deletes file but not DB entry
        
        photos.delete()  # Delete DB entries
        
        # Remove the event folder if empty
        if os.path.exists(event_folder) and not os.listdir(event_folder):
            os.rmdir(event_folder)

        event.delete()  # Delete event
        messages.success(request, "Event and associated photos deleted successfully!")
        return redirect(reverse("photographer"))

    return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))

# delete only photos of the event
def delete_event_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if request.method == "POST":
        photos = Photo.objects.filter(event=event)
        
        for photo in photos:
            if photo.image:
                photo.image.delete(save=False)
        
        photos.delete()  # Delete DB entries
        messages.success(request, "All photos of the event have been deleted successfully!")
        return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))

    return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))
