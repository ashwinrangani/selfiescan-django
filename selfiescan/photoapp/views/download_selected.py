from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.paginator import Paginator
from ..models import Event, EventShare, Photo
import logging
import zipfile
from io import BytesIO
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

# download selected photos chosen by customer as zip
@login_required
def download_selected_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id, photographer=request.user)
    selected_photos = Photo.objects.filter(event=event, customer_selected=True)

    if not selected_photos.exists():
        return HttpResponse("No photos selected by the customer.", status=400)

    # Create a ZIP file in memory
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for photo in selected_photos:
            # Use the original image
            file_path = photo.image.path
            file_name = f"photo_{photo.display_number}.jpg"  # Customize filename as needed
            try:
                with open(file_path, 'rb') as f:
                    zip_file.writestr(file_name, f.read())
            except FileNotFoundError:
                logger.error(f"Photo file not found: {file_path}")
                continue

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{event.name}_selected_photos.zip"'
    return response