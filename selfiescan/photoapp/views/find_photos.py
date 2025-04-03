from django.shortcuts import get_object_or_404, render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import face_recognition
import numpy as np
from django.http import JsonResponse
from ..models import FaceEncoding,Event
import logging

logger = logging.getLogger(__name__)

def find_matches(selfie_path,event_id, threshold=0.5):
    selfie_image = face_recognition.load_image_file(selfie_path)
    selfie_encodings = face_recognition.face_encodings(selfie_image)
    
    if not selfie_encodings:
        logger.warning("No face detected in uploaded selfie")
        return []

    target_encoding = selfie_encodings[0]  
    
    all_face_encodings = FaceEncoding.objects.filter(photo__event__event_id=event_id)

    if not all_face_encodings.exists():
        logger.info(f"No encodings found for event {event_id}")
        return []
    
    matched_photos = set()

    for embedding in all_face_encodings:
        stored_encoding = np.frombuffer(embedding.encoding, dtype=np.float64)
        distance = face_recognition.face_distance([stored_encoding], target_encoding)
        
        # Extract the scalar value from the distance array
        distance_scalar = float(distance[0])  # Convert NumPy array to a single float
        
        if distance_scalar <= threshold:
            matched_photos.add((embedding.photo.image.url, distance_scalar))  # Use scalar value

    # Sort by best match (lower distance = better match)
    return sorted(matched_photos, key=lambda x: x[1])

def process_selfie(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)
    
    if request.method == 'POST':
        selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
        if selfie:
            fs = FileSystemStorage()
            filename = fs.save(selfie.name, selfie)
            selfie_path = fs.path(filename)

            try:
                matching_images = find_matches(selfie_path,event_id)
                if matching_images is None:  # Handle case where no faces are detected
                    matching_images = []
                
                return JsonResponse({
                    'message': 'Matching photos found' if matching_images else 'Matching photos not found',
                    'matches': [{'path': match[0], 'distance': float(match[1])} for match in matching_images]
                })

            except Exception as e:
                logger.error(f"Error in process_selfie: {e}")
                return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
            finally:
                if os.path.exists(selfie_path):
                    os.remove(selfie_path)

        return JsonResponse({'message': 'No file uploaded'}, status=400)

    return render(request, 'find_photos.html',{'event': event})