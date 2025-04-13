from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
import os
import face_recognition
import numpy as np
from PIL import Image
from ..models import FaceEncoding, Event, Photo
import logging

logger = logging.getLogger(__name__)

def find_matches(selfie_path, event_id, tolerance=0.45):
    # Load and process selfie
    pil_image = Image.open(selfie_path).convert('RGB')
    image = np.array(pil_image)
    
    # Step 1: Find selfie faces
    selfie_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2)
    logger.info(f"Selfie face locations: {selfie_locations}")
    
    if not selfie_locations:
        logger.warning("No face detected in uploaded selfie")
        return []

    # Step 2: Estimate selfie landmarks (for logging/debugging)
    selfie_landmarks = face_recognition.face_landmarks(image, selfie_locations)
    if not selfie_landmarks:
        logger.warning("No face landmarks detected for selfie")
    else:
        logger.info(f"Selfie landmarks detected for {len(selfie_landmarks)} faces")

    # Step 3: Encode selfie
    selfie_encodings = []
    for idx, loc in enumerate(selfie_locations):
        encoding = face_recognition.face_encodings(image, [loc])[0]
        selfie_encodings.append(encoding)
        logger.info(f"Selfie encoding sample: {encoding[:5]}...")
    
    if not selfie_encodings:
        logger.warning("No face encoding generated for selfie")
        return []
    
    selfie_encoding = selfie_encodings[0]

    # Get known encodings
    all_face_encodings = FaceEncoding.objects.filter(photo__event__event_id=event_id)
    known_encodings = [np.frombuffer(encoding.encoding, dtype=np.float64) for encoding in all_face_encodings]
    known_photos = [encoding.photo.image.url for encoding in all_face_encodings]

    if not known_encodings:
        logger.warning(f"No known face encodings found for event {event_id}")
        return []

    # Step 4: Compare with distances
    distances = face_recognition.face_distance(known_encodings, selfie_encoding)
    logger.info(f"Face distances: {distances}")
    
    # Determine matches based on tolerance
    matched_photos = []
    for idx, distance in enumerate(distances):
        if distance <= tolerance:
            matched_photos.append((known_photos[idx], float(distance)))

    return matched_photos

def process_selfie(request, event_id):
    
    event = get_object_or_404(Event, event_id=event_id)
    unprocessed_photos = Photo.objects.filter(event__event_id=event_id, is_processed = False)
    
    if unprocessed_photos.exists():
        return JsonResponse({
            'message': f'Kindly wait for some time, {unprocessed_photos.count()} photos are still being processed.',
            'pending_count': unprocessed_photos.count()
        }, status=202)
    
    if request.method == 'POST':
        selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
        if selfie:
            fs = FileSystemStorage()
            filename = fs.save(selfie.name, selfie)
            selfie_path = fs.path(filename)

            try:
                matching_images = find_matches(selfie_path, event_id)
                if matching_images is None:
                    matching_images = []
                
                return JsonResponse({
                    'message': 'Matching photos found' if matching_images else 'Matching photos not found',
                    'matches': [{'path': match[0], 'distance': match[1]} for match in matching_images]
                })

            except Exception as e:
                logger.error(f"Error in process_selfie: {e}")
                return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
            finally:
                if os.path.exists(selfie_path):
                    os.remove(selfie_path)

        return JsonResponse({'message': 'No file uploaded'}, status=400)

    return render(request, 'find_photos.html', {'event': event})



# from django.shortcuts import render, get_object_or_404
# from django.core.files.storage import FileSystemStorage
# from django.http import JsonResponse
# import os
# import face_recognition
# import numpy as np
# from ..models import FaceEncoding, Event
# import logging

# logger = logging.getLogger(__name__)

# def find_matches(selfie_path, event_id, threshold=0.6):
#     selfie_image = face_recognition.load_image_file(selfie_path)
#     selfie_encodings = face_recognition.face_encodings(selfie_image)
    
#     if not selfie_encodings:
#         logger.warning("No face detected in uploaded selfie")
#         return []

#     target_encoding = selfie_encodings[0]
#     # Filter by event_id (UUID)
#     all_face_encodings = FaceEncoding.objects.filter(photo__event__event_id=event_id)
    
#     if not all_face_encodings.exists():
#         logger.info(f"No encodings found for event {event_id}")
#         return []

#     matched_photos = set()
#     for embedding in all_face_encodings:
#         stored_encoding = np.frombuffer(embedding.encoding, dtype=np.float64)
#         distance = face_recognition.face_distance([stored_encoding], target_encoding)
#         distance_scalar = float(distance[0])
#         if distance_scalar <= threshold:
#             matched_photos.add((embedding.photo.image.url, distance_scalar))
    
#     return sorted(matched_photos, key=lambda x: x[1])

# def process_selfie(request, event_id):
#     event = get_object_or_404(Event, event_id=event_id)
    
#     if request.method == 'POST':
#         selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
#         if not selfie:
#             return JsonResponse({'message': 'No file uploaded'}, status=400)
        
#         fs = FileSystemStorage()
#         filename = fs.save(selfie.name, selfie)
#         selfie_path = fs.path(filename)
        
#         try:
#             matching_images = find_matches(selfie_path, event_id)
#             return JsonResponse({
#                 'message': 'Matching photos found' if matching_images else 'Matching photos not found',
#                 'matches': [{'path': match[0], 'distance': float(match[1])} for match in matching_images]
#             })
#         except Exception as e:
#             logger.error(f"Error in process_selfie: {e}")
#             return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
#         finally:
#             if os.path.exists(selfie_path):
#                 os.remove(selfie_path)
    
#     return render(request, 'find_photos.html', {'event': event})
