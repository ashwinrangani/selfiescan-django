from celery import shared_task
import face_recognition
import numpy as np
from PIL import Image

@shared_task
def process_photo(photo_id):
    from .models import Photo, FaceEncoding  # To prevent cyclic imports
    
    try:
        photo = Photo.objects.get(id=photo_id)
        image_path = photo.image.path
        image = face_recognition.load_image_file(image_path)
        if image is None:
            return f"Failed to load image for photo {photo_id}"

        # Extract all face encodings
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)
        print(f"Detected {len(face_locations)} faces")
        if face_encodings:
            for encoding in face_encodings:
                FaceEncoding.objects.create(
                    photo=photo, 
                    encoding=np.array(encoding).tobytes()
                )
            return f"Photo {photo_id} processed successfully"
        else:
            return f"No face found in photo {photo_id}"

    except Photo.DoesNotExist:
        return f"Photo {photo_id} not found"
    except Exception as e:
        return f"Error processing photo {photo_id}: {str(e)}"