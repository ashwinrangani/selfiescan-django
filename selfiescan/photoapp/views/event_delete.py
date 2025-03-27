from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from ..models import Event, Photo

# delete event with all photos
def event_delete(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)
    
    if request.method == "POST":
        Photo.objects.filter(event=event).delete()
        event.delete()
        messages.success(request, "Event and associated photos deleted successfully!")
        return redirect(reverse("photographer"))

    return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))

# delete only photos of the event
def delete_event_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if request.method == "POST":
        Photo.objects.filter(event=event).delete()
        messages.success(request, "All photos of the event have been deleted successfully!")
        return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))

    return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))