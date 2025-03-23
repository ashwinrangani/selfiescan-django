from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from ..models import Event, Photo
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def event_detail(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    # Handle event updates (POST)
    if request.method == "POST":
        new_name = request.POST.get("name", event.name)
        new_date = request.POST.get("date", event.date)
        new_location = request.POST.get("location", event.location)

        # Check if the event name is unique
        if event.name != new_name and Event.objects.filter(name=new_name).exists():
            messages.error(request, "An event with this name already exists. Please choose a different name.")
        else:
            event.name = new_name
            event.date = new_date
            event.location = new_location
            event.save()
            messages.success(request, "Event updated successfully!")
            return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))

    # === Handle photo display with pagination ===
    photos = Photo.objects.filter(event=event)

    # Set up pagination (10 photos per page)
    page = request.GET.get("page", 1)
    paginator = Paginator(photos, 10)

    try:
        photos = paginator.page(page)
    except PageNotAnInteger:
        photos = paginator.page(1)
    except EmptyPage:
        photos = paginator.page(paginator.num_pages)

    # Render event details and photos together
    return render(
        request,
        "event_detail.html",
        {"event": event, "photos": photos},
    )
