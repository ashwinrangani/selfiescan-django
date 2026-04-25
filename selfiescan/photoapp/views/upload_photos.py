from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden
from ..models import Event
import logging
logger = logging.getLogger(__name__)

@login_required
def upload_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if event.photographer != request.user:
        return HttpResponseForbidden("You don't have access to this event.")

    return render(request, 'upload_photos.html', {"event": event})

