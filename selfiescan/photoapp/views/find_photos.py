from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
import os
import face_recognition
import numpy as np
from PIL import Image
from ..models import FaceEncoding, Event, Photo
import logging
import cv2

def resize_image_for_processing(image, max_width=800):
    height, width = image.shape[:2]
    if width > max_width:
        scaling_factor = max_width / width
        new_size = (int(width * scaling_factor), int(height * scaling_factor))
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    return image

logger = logging.getLogger(__name__)

def find_matches(selfie_path, event_id, tolerance=0.465):
    # Load and process selfie
    image = cv2.imread(selfie_path)
    
    if image is None:
            return f"Failed to load image for photo {selfie_path}"
   
    resized_image = resize_image_for_processing(image)
    image = np.array(resized_image)
    # Step 1: Detect faces in selfie
    selfie_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2)
    logger.info(f"Detected {len(selfie_locations)} face locations: {selfie_locations}")

    if not selfie_locations:
        logger.warning("No face detected in uploaded selfie")
        return []

    # Step 2: Encode all faces from the selfie
    selfie_encodings = []
    for idx, loc in enumerate(selfie_locations):
        encoding = face_recognition.face_encodings(image, [loc])[0]
        selfie_encodings.append(encoding)
        logger.info(f"Selfie encoding {idx} sample: {encoding[:5]}...")

    if not selfie_encodings:
        logger.warning("No face encoding generated for selfie")
        return []

    # Step 3: Fetch known encodings from DB
    all_face_encodings = FaceEncoding.objects.filter(photo__event__event_id=event_id)
    known_encodings = [np.frombuffer(enc.encoding, dtype=np.float64) for enc in all_face_encodings]
    known_photos = [enc.photo.image.url for enc in all_face_encodings]

    if not known_encodings:
        logger.warning(f"No known face encodings found for event {event_id}")
        return []

    known_encodings_np = np.array(known_encodings)
    logger.info(f"Comparing {len(selfie_encodings)} selfie encodings to {len(known_encodings_np)} known encodings")

    # Step 4: Match each selfie encoding
    best_matches = {}
    for selfie_encoding in selfie_encodings:
        distances = np.linalg.norm(known_encodings_np - selfie_encoding, axis=1)
        for idx, distance in enumerate(distances):
            if distance <= tolerance:
                url = known_photos[idx]
                if url not in best_matches or distance < best_matches[url]:
                    best_matches[url] = float(distance)

    # Step 5: Return as list of (photo_url, distance)
    matched_photos = [(url, dist) for url, dist in best_matches.items()]
    matched_photos.sort(key=lambda x: x[1])  # Sort by distance (lower = better match)
    logger.info(f"Total matched photos: {len(matched_photos)}")
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
