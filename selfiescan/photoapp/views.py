from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import pickle
import face_recognition
import logging

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


# Create your views here.
def upload_selfie(request):
    if request.method == 'POST':
        selfie = request.FILES.get('selfie') or request.FILES.get('camera_selfie')
        if selfie:
            fs = FileSystemStorage()
            filename = fs.save(selfie.name, selfie)
            selfie_path = fs.path(filename)
            

            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of current file
                encodings_file = os.path.join(base_dir, 'encodings.pkl')

                matching_images = find_matches(selfie_path, encodings_file)
                
                if matching_images:
                    return render(request, 'upload_selfie.html', {
                        'message': 'Matching photos found',
                        'matches': matching_images,  # List of tuples (path, distance)
                        'selfie_url': fs.url(filename),
                    })

                else:
                    return render(request, 'upload_selfie.html', {
                        'message': 'No matching photos found',
                        'selfie_url': fs.url(filename),
                    })
                    print("Media URLs for matches:", [settings.MEDIA_URL + match for match in matching_images])


            except Exception as e:
                return render(request, 'upload_selfie.html', {
                    'message': f'Error during face recognition: {str(e)}',
                    'selfie_url': fs.url(filename),
                })

    return render(request, 'upload_selfie.html')  # Render the upload form for GET requests
  

def generate_barcode():
    pass