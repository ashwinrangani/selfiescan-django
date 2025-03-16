from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from ..forms import EventRegistration
from ..models import Event, Photo

@login_required
def create_event(request):
    if request.method == "POST":
        form = EventRegistration(request.POST)
        if form.is_valid():
            event = form.save(commit=False)  # Save without committing
            event.photographer = request.user  # Assign photographer
            event.save()  # Now save the event
            return redirect('photographer')
    
    else:
        form = EventRegistration()  # No POST data for GET requests
    events = Event.objects.filter(photographer=request.user)
    stats = {
        "total_events": events.count(),
        "total_uploads": Photo.objects.filter(event__in=events).count(),
        # "total_searches": SearchQuery.objects.filter(event__in=events).count(),
    }
    return render(request, "photographer.html", {"form": form, "events": events, "stats": stats})

def download_qr(request, event_id):
    event = get_object_or_404(Event, event_id = event_id)
    if event.qr_code:
        return FileResponse(event.qr_code.open(), as_attachment=True, filename=f"{event.name}_QR.png")
    return HttpResponse("QR Code not found.", status=404)