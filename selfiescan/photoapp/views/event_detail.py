from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from ..models import Event, Photo
from django.contrib import messages
from django.core.paginator import Paginator,PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.template.loader import render_to_string

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

    photos_list = Photo.objects.filter(event=event).order_by('-id')  # Adjust ordering as needed
    photos_count = photos_list.count()
    
    # Set up pagination - 12 photos per page is typical for a grid
    paginator = Paginator(photos_list, 12)
    page = request.GET.get('page', 1)
    photos = paginator.get_page(page)
    
    return render(request, "event_detail.html", {
        "event": event, 
        "num_photos": photos_count,
        "photos": photos
    })



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
