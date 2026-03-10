from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ...models import Event, SubEvent
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def create_session(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if event.photographer != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    name = request.POST.get("name")
    date = request.POST.get("date")

    if not name:
        return JsonResponse({"error": "Name required"}, status=400)

    session = SubEvent.objects.create(
        event=event,
        name=name,
        date=date if date else None
    )

    return JsonResponse({
        "id": session.id,
        "name": session.name,
        "date": session.date,
        "photo_count": 0,
        "success": True,
    })

@login_required
@require_POST
def edit_session(request, event_id, pk):
    event = get_object_or_404(Event, event_id=event_id)
    session = get_object_or_404(SubEvent, pk=pk, event=event)

    if event.photographer != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    name = request.POST.get("name")
    date = request.POST.get("date")

    if not name:
        return JsonResponse({"error": "Name required"}, status=400)

    session.name = name
    session.date = date if date else None
    session.save()

    return JsonResponse({
        "id": session.id,
        "name": session.name,
        "date": session.date,
        "photo_count": session.photos.count(),
        "success": True,
    })

@login_required
@require_POST
def delete_session(request, event_id, pk):
    event = get_object_or_404(Event, event_id=event_id)
    session = get_object_or_404(SubEvent, pk=pk, event=event)

    if event.photographer != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    session.delete()

    return JsonResponse({"success": True, "id": str(session.id),})
