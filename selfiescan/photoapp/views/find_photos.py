# find_photos.py (modified)
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
import os
import face_recognition
import numpy as np
from ..models import FaceEncoding, Event, Photo, SiteStats
import logging
import cv2
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
import tempfile
from PIL import Image
from django.db.models import F

# Initialize Rekognition client
rekognition = boto3.client(
    'rekognition',
    region_name='ap-south-1',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

def resize_image_for_processing(image, max_width=600):
    height, width = image.shape[:2]
    if width > max_width:
        scaling_factor = max_width / width
        new_size = (int(width * scaling_factor), int(height * scaling_factor))
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    return image

logger = logging.getLogger(__name__)

def find_matches(selfie_path, event_id, tolerance=0.55):
    # Temporary upload to S3 for Rekognition (since it prefers S3 objects)
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    s3_key = f"temp_selfies/{os.path.basename(selfie_path)}_{event_id}"
    s3 = boto3.client('s3', region_name='ap-south-1')
    
    # Upload selfie to S3 temporarily
    
    try:
        s3.upload_file(selfie_path, bucket, s3_key)
        selfie_s3_url = f"s3://{bucket}/{s3_key}"
        logger.info(f"Selfie uploaded to S3: {selfie_s3_url}")
    except Exception as upload_e:
        logger.error(f"Failed to upload selfie to S3: {upload_e}")
        selfie_s3_url = None

    # Rekognition: Search faces
    use_rekognition = True
    matched_photos = []
    try:
        if selfie_s3_url:
            collection_id = f"event_{event_id}"
            
            # Search faces in selfie against collection
            search_response = rekognition.search_faces_by_image(
                CollectionId=collection_id,
                Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
                FaceMatchThreshold=86  # Confidence threshold (adjust as needed)
            )
            
            if 'FaceMatches' in search_response:
                for match in search_response['FaceMatches']:
                    # ExternalImageId is our photo.id
                    photo_id = int(match['Face']['ExternalImageId'])
                    similarity = match['Similarity']  # 0-100 score
                    matched_photos.append((photo_id, (100 - similarity) / 100))  # Normalize to distance-like (lower better)
                    logger.info(f"Rekognition match: photo {photo_id} with similarity {similarity}%")
            
            if matched_photos:
                matched_photos.sort(key=lambda x: x[1])  # Sort by 'distance'
                logger.info(f"Rekognition found {len(matched_photos)} matches")
                return matched_photos
        
    except (ClientError, NoCredentialsError) as e:
        logger.warning(f"Rekognition search failed for event {event_id}: {e}. Falling back to face_recognition.")
        use_rekognition = False
    finally:
        # Clean up temp S3 file
        if selfie_s3_url:
            try:
                s3.delete_object(Bucket=bucket, Key=s3_key)
            except:
                pass

    # Fallback to face_recognition
    if not use_rekognition or not matched_photos:
        image = cv2.imread(selfie_path)
        if image is None:
            return f"Failed to load image for photo {selfie_path}"
        
        resized_image = resize_image_for_processing(image)
        image = np.array(resized_image)
        # Step 1: Detect faces in selfie
        selfie_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2)
        logger.info(f"Fallback: Detected {len(selfie_locations)} face locations: {selfie_locations}")

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
                    if photo_id not in best_matches or distance < best_matches[photo_id]:
                        best_matches[photo_id] = float(distance)

        # Step 5: Return as list of (photo_url, distance)
        matched_photos = [(photo_id, dist) for photo_id, dist in best_matches.items()]
        matched_photos.sort(key=lambda x: x[1])  # Sort by distance (lower = better match)
        logger.info(f"Fallback: Total matched photos: {len(matched_photos)}")
        return matched_photos

    return matched_photos


def process_selfie(request, event_id):
    
    event = get_object_or_404(Event, event_id=event_id)
    
    unprocessed_photos = Photo.objects.filter(event__event_id=event_id, is_processed = False)
    
    if unprocessed_photos.exists():
        return render(request, 'find_photos.html', {
            'message': f'Kindly wait for some time, {unprocessed_photos.count()} photos are still being processed.',
            'pending_count': unprocessed_photos.count(),
            'event':event
        }, status=202)
    
    # Check for unbranded photos if branding is enabled
    if event.branding_enabled:
        unbranded_photos = Photo.objects.filter(event__event_id=event_id, is_branded=False)
        if unbranded_photos.exists():
            return render(request, 'find_photos.html',{
                'message': f'Kindly wait for some time, {unbranded_photos.count()} photos are still being branded.',
                'pending_count': unbranded_photos.count()
            }, status=202)
        
    if request.method == 'POST':
        print("FILES received:", request.FILES, flush=True)
        print("FILES keys:", request.FILES.keys(), flush=True)

        logger.debug("FILES received: %s", request.FILES)
        logger.debug("Files keys: %s", request.FILES.keys())
        selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
        if selfie:
            print("Selfie found:", selfie.name, selfie.content_type, selfie.size)
            if not selfie.content_type.startswith('image/'):
                return JsonResponse({'message': 'Invalid file type'}, status=400)
            if selfie.size > 10 * 1024 * 1024:
                return JsonResponse({'message': 'File too large'}, status=400)
            
            fs = FileSystemStorage()
            filename = fs.save(selfie.name, selfie)
            selfie_path = fs.path(filename)

            try:
                matching_images = find_matches(selfie_path, event_id)
                if matching_images is None:
                    matching_images = []
                matches = []   
                for photo_id, distance in matching_images:
                    photo = Photo.objects.get(id=photo_id)
                    # Serve branded photo if branding is enabled and available, otherwise original
                    photo_url = photo.branded_image.url if event.branding_enabled and photo.is_branded and photo.branded_image else photo.image.url
                    matches.append({"path": photo_url, "distance": distance})

                # Update query counter
                SiteStats.objects.filter(photographer=event.photographer).update(
                total_face_search_queries=F('total_face_search_queries') + 1
                )
                
                return JsonResponse({
                    'message': 'Matching photos found' if matching_images else 'Matching photos not found',
                    'matches': matches
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
# from ..models import FaceEncoding, Event, Photo
# import logging
# import cv2


# def resize_image_for_processing(image, max_width=600):
#     height, width = image.shape[:2]
#     if width > max_width:
#         scaling_factor = max_width / width
#         new_size = (int(width * scaling_factor), int(height * scaling_factor))
#         image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
#     return image

# logger = logging.getLogger(__name__)

# def find_matches(selfie_path, event_id, tolerance=0.55):
#     # Load and process selfie
#     image = cv2.imread(selfie_path)
    
#     if image is None:
#             return f"Failed to load image for photo {selfie_path}"
   
#     resized_image = resize_image_for_processing(image)
#     image = np.array(resized_image)
#     # Step 1: Detect faces in selfie
#     selfie_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2)
#     logger.info(f"Detected {len(selfie_locations)} face locations: {selfie_locations}")

#     if not selfie_locations:
#         logger.warning("No face detected in uploaded selfie")
#         return []

#     # Step 2: Encode all faces from the selfie
#     selfie_encodings = []
#     for idx, loc in enumerate(selfie_locations):
#         encoding = face_recognition.face_encodings(image, [loc])[0]
#         selfie_encodings.append(encoding)
#         logger.info(f"Selfie encoding {idx} sample: {encoding[:5]}...")

#     if not selfie_encodings:
#         logger.warning("No face encoding generated for selfie")
#         return []

#     # Step 3: Fetch known encodings from DB
#     all_face_encodings = FaceEncoding.objects.filter(photo__event__event_id=event_id)

#     known_encodings = [np.frombuffer(enc.encoding, dtype=np.float64) for enc in all_face_encodings]
#     known_photo_ids = [enc.photo.id for enc in all_face_encodings]

#     if not known_encodings:
#         logger.warning(f"No known face encodings found for event {event_id}")
#         return []

#     known_encodings_np = np.array(known_encodings)
#     logger.info(f"Comparing {len(selfie_encodings)} selfie encodings to {len(known_encodings_np)} known encodings")

#     # Step 4: Match each selfie encoding
#     best_matches = {}
#     for selfie_encoding in selfie_encodings:
#         distances = np.linalg.norm(known_encodings_np - selfie_encoding, axis=1)
#         for idx, distance in enumerate(distances):
#             if distance <= tolerance:
#                 photo_id = known_photo_ids[idx]
#                 if photo_id not in best_matches or distance < best_matches[photo_id]: best_matches[photo_id] = float(distance)

#     # Step 5: Return as list of (photo_url, distance)
#     matched_photos = [(photo_id, dist) for photo_id, dist in best_matches.items()]
#     matched_photos.sort(key=lambda x: x[1])  # Sort by distance (lower = better match)
#     logger.info(f"Total matched photos: {len(matched_photos)}")
#     return matched_photos



# def process_selfie(request, event_id):
    
#     event = get_object_or_404(Event, event_id=event_id)
    
#     unprocessed_photos = Photo.objects.filter(event__event_id=event_id, is_processed = False)
    
#     if unprocessed_photos.exists():
#         return render(request, 'find_photos.html', {
#             'message': f'Kindly wait for some time, {unprocessed_photos.count()} photos are still being processed.',
#             'pending_count': unprocessed_photos.count(),
#             'event':event
#         }, status=202)
    
#     # Check for unbranded photos if branding is enabled
#     if event.branding_enabled:
#         unbranded_photos = Photo.objects.filter(event__event_id=event_id, is_branded=False)
#         if unbranded_photos.exists():
#             return render(request, 'find_photos.html',{
#                 'message': f'Kindly wait for some time, {unbranded_photos.count()} photos are still being branded.',
#                 'pending_count': unbranded_photos.count()
#             }, status=202)
        
#     if request.method == 'POST':
#         print("FILES received:", request.FILES, flush=True)
#         print("FILES keys:", request.FILES.keys(), flush=True)

#         logger.debug("FILES received: %s", request.FILES)
#         logger.debug("Files keys: %s", request.FILES.keys())
#         selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
#         if selfie:
#             print("Selfie found:", selfie.name, selfie.content_type, selfie.size)
#             if not selfie.content_type.startswith('image/'):
#                 return JsonResponse({'message': 'Invalid file type'}, status=400)
#             if selfie.size > 10 * 1024 * 1024:
#                 return JsonResponse({'message': 'File too large'}, status=400)
            
#             fs = FileSystemStorage()
#             filename = fs.save(selfie.name, selfie)
#             selfie_path = fs.path(filename)

#             try:
#                 matching_images = find_matches(selfie_path, event_id)
#                 if matching_images is None:
#                     matching_images = []
#                 matches = []   
#                 for photo_id, distance in matching_images:
#                     photo = Photo.objects.get(id=photo_id)
#                     # Serve branded photo if branding is enabled and available, otherwise original
#                     photo_url = photo.branded_image.url if event.branding_enabled and photo.is_branded and photo.branded_image else photo.image.url
#                     matches.append({"path": photo_url, "distance": distance})

#                 return JsonResponse({
#                     'message': 'Matching photos found' if matching_images else 'Matching photos not found',
#                     'matches': matches
#                 })
#             except Exception as e:
#                 logger.error(f"Error in process_selfie: {e}")
#                 return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
#             finally:
#                 if os.path.exists(selfie_path):
#                     os.remove(selfie_path)

#         return JsonResponse({'message': 'No file uploaded'}, status=400)

#     return render(request, 'find_photos.html', {'event': event})
