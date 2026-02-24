from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from ..models import Event
import json

@login_required
@require_POST
def toggle_find_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id, photographer=request.user)
    data = json.loads(request.body)
    is_enabled = data.get('is_enabled', False)
    event.is_find_photos_enabled = is_enabled
    event.save()

    return JsonResponse({
        'success': True,
        'message': f"Downloads {'enabled' if event.is_find_photos_enabled == True else 'disabled'} for end users."
    })
