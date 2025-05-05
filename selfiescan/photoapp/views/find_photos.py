from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
import os
import face_recognition
import numpy as np
from ..models import FaceEncoding, Event, Photo
import logging
import cv2
from django.urls import reverse

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
    known_photo_ids = [enc.photo.id for enc in all_face_encodings]

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
                photo_id = known_photo_ids[idx]
                if photo_id not in best_matches or distance < best_matches[photo_id]: best_matches[photo_id] = float(distance)

    # Step 5: Return as list of (photo_url, distance)
    matched_photos = [(photo_id, dist) for photo_id, dist in best_matches.items()]
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
                    'matches': [
                        {
                            'path': reverse('serve_branded_photo', args=[photo_id]) if event.branding_enabled 
                                    else Photo.objects.get(id=photo_id).image.url,
                            'distance': distance
                        }
                        for photo_id, distance in matching_images
                    ]
                })


            except Exception as e:
                logger.error(f"Error in process_selfie: {e}")
                return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
            finally:
                if os.path.exists(selfie_path):
                    os.remove(selfie_path)
                    

        return JsonResponse({'message': 'No file uploaded'}, status=400)

    return render(request, 'find_photos.html', {'event': event})