from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from ..models import Event, Photo

def upload_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    if request.method == 'POST':
        upload_data = request.FILES.getlist('upload_data')

        if not upload_data:
            return JsonResponse({"message": "No photos uploaded"}, status=400)

        saved_data = []
        for data in upload_data:
            photo = Photo(event=event, image=data)
            photo.save()  # `post_save` will trigger Celery task
            saved_data.append(photo.image.url)

        return JsonResponse({
            "upload_success": True,
            "uploaded_images": len(saved_data),
            "files": saved_data
        })

    return render(request, 'upload_photos.html', {"event": event})
