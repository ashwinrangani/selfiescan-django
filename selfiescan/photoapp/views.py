from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import pickle
import face_recognition
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def find_matches(selfie_path, encodings_file='encodings.pkl', thresold=0.9):
    selfie_image = face_recognition.load_image_file(selfie_path)
    selfie_encoding = face_recognition.face_encodings(selfie_image)

    if not selfie_encoding:
        return []
    
    selfie_encoding = selfie_encoding[0]
    with open(encodings_file, 'rb') as f:
        data = pickle.load(f)
        encodings = data['encodings']
        identities = data['identities']
    
    matches = []
    distances = face_recognition.face_distance(encodings, selfie_encoding)

    for i, distance in enumerate(distances):
        if distance <= thresold:  # Match Found
            path = os.path.relpath(identities[i], settings.MEDIA_ROOT)
            matches.append((path, distance))
    
    matches = sorted(matches, key=lambda x: x[1])  # Sort by distance
    return matches  # Return a list of tuples (relative_path, distance)


def upload_selfie(request):
    if request.method == 'POST':
        selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
        if selfie:
            fs = FileSystemStorage()
            filename = fs.save(selfie.name, selfie)
            selfie_path = fs.path(filename)

            try:
                # Assuming you have a `find_matches` function for face recognition
                base_dir = os.path.dirname(os.path.abspath(__file__))
                encodings_file = os.path.join(base_dir, 'encodings.pkl')

                matching_images = find_matches(selfie_path, encodings_file)

                return JsonResponse({
                    'message': 'Matching photos found' if matching_images else 'Matching photos not found',
                    'matches': [{'path': settings.MEDIA_URL + match[0], 'distance': match[1]} for match in matching_images]
                })

            except Exception as e:
                return JsonResponse({'message': f'Error: {str(e)}'}, status=500)

        return JsonResponse({'message': 'No file uploaded'}, status=400)

    # Render the template on GET request
    return render(request, 'upload_selfie.html')

def generate_barcode():
    pass