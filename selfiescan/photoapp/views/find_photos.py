from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import pickle
import face_recognition
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def find_matches(selfie_path, encodings_file='encodings.pkl', threshold=0.5):  # Lower threshold
    selfie_image = face_recognition.load_image_file(selfie_path)
    
    # Get all detected faces    
    selfie_encodings = face_recognition.face_encodings(selfie_image)

    if not selfie_encodings:
        return []
    
    with open(encodings_file, 'rb') as f:
        data = pickle.load(f)
        encodings = data['encodings']
        identities = data['identities']
    
    matches = set()
    
    for selfie_encoding in selfie_encodings:  # Loop through detected faces
        distances = face_recognition.face_distance(encodings, selfie_encoding)

        for i, distance in enumerate(distances):
            if distance <= threshold:
                path = os.path.relpath(identities[i], settings.MEDIA_ROOT)
                matches.add((path, distance))
    
    matches = sorted(matches, key=lambda x: x[1])  # sorted by the second element distance in matches tuple
    return matches



def process_selfie(request):
    if request.method == 'POST':
        
        selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
        if selfie:
            fs = FileSystemStorage()
            filename = fs.save(selfie.name, selfie)
            selfie_path = fs.path(filename)
            print(selfie_path)

            try:
                encodings_file = str(settings.BASE_DIR) + '/photoapp/encodings.pkl'
               
                matching_images = find_matches(selfie_path, encodings_file)

                return JsonResponse({
                    'message': 'Matching photos found' if matching_images else 'Matching photos not found',
                    'matches': [{'path': settings.MEDIA_URL + match[0], 'distance': match[1]} for match in matching_images]
                })

            except Exception as e:
                logger.error(f"Error in upload_selfie: {e}")
                return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
            finally:
                if os.path.exists(selfie_path):
                    os.remove(selfie_path)
                    print(f"Deleted temporary selfie file: {selfie_path}")
                    

        return JsonResponse({'message': 'No file uploaded'}, status=400)

    # Render the template on GET request
    return render(request, 'find_photos.html')
