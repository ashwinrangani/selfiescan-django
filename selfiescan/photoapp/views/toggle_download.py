from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from ..models import Event
import json

@login_required
@require_POST
def toggle_download(request, event_id):
    event = get_object_or_404(Event, event_id=event_id, photographer=request.user)
    data = json.loads(request.body)
    is_downloadable = data.get('is_downloadable', False)
    print(is_downloadable)
    event.is_downloadable = is_downloadable
    event.save()

    return JsonResponse({
        'success': True,
        'message': f"Downloads {'enabled' if event.is_downloadable == True else 'disabled'} for end users."
    })