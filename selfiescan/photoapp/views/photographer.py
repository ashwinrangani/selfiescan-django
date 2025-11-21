from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from ..forms import EventRegistration
from ..models import Event, Photo,SiteStats
from django.contrib import messages
from django.conf import settings
import boto3

@login_required
def create_event(request):
    if request.method == "POST":
        form = EventRegistration(request.POST)
        if form.is_valid():
            event_name = form.cleaned_data["name"]

            # Check if event with this name already exists for the user
            if Event.objects.filter(photographer=request.user, name=event_name).exists():
                messages.error(request, f"An event with the name '{event_name}' already exists. Please choose a different name.")
                return redirect('photographer')

            # Save the event if no duplicate is found
            event = form.save(commit=False)
            event.photographer = request.user
            event.save()
            messages.success(request, "Event created successfully!")
            return redirect('photographer')

    else:
        form = EventRegistration()

    # Get user's events and statistics
    events = Event.objects.filter(photographer=request.user)
    stats = SiteStats.objects.first()
    total_queries = stats.total_face_search_queries if stats else 0

    stats = {
        "total_events": events.count(),
        "total_uploads": Photo.objects.filter(event__in=events).count(),
        "total_queries": total_queries,
    }

    return render(request, "photographer.html", {"form": form, "events": events, "stats": stats})

def download_qr(request, event_id):
    event = get_object_or_404(Event, event_id = event_id)
    if event.qr_code:
        return FileResponse(event.qr_code.open(), as_attachment=True, filename=f"{event.name}_QR.png")
    return HttpResponse("QR Code not found.", status=404)


@login_required
def get_storage_usage(request):
    user = request.user
    s3 = boto3.client("s3")

    prefix = f"photos/{user.username}/"
    total_bytes = 0

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix):
        for obj in page.get("Contents", []):
            total_bytes += obj["Size"]

    total_mb = round(total_bytes / (1024 * 1024), 2)
    return JsonResponse({"usage": total_mb})