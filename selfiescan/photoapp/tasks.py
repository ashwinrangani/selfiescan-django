from celery import shared_task
import face_recognition
import numpy as np
from PIL import Image, ImageDraw
import os
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_photo(photo_id):
    from .models import Photo, FaceEncoding
    
    try:
        photo = Photo.objects.get(id=photo_id)
        image_path = photo.image.path
        
        pil_image = Image.open(image_path).convert('RGB')
        image = np.array(pil_image)
        
        if image is None:
            return f"Failed to load image for photo {photo_id}"

        face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1)
        logger.info(f"Detected {len(face_locations)} face locations: {face_locations}")
        
        if not face_locations:
            logger.warning(f"No faces detected in {image_path}. Marking as processed.")
            photo.is_processed = True
            photo.save()
            return f"No face found in photo {photo_id}"

        
        face_encodings = []
        for idx, location in enumerate(face_locations):
            encoding = face_recognition.face_encodings(image, [location])[0]
            face_encodings.append(encoding)
            logger.info(f"Encoding for face {idx} sample: {encoding[:5]}...")

        # Draw boxes on the image for verification
        # draw = ImageDraw.Draw(pil_image)
        # for (top, right, bottom, left) in face_locations:
        #     draw.rectangle([left, top, right, bottom], outline="red", width=2)
        
        # Save the annotated image
        # annotated_path = os.path.join(os.path.dirname(image_path), f"annotated_{os.path.basename(image_path)}")
        # pil_image.save(annotated_path)
        # logger.info(f"Annotated image saved at {annotated_path}")

        
        if face_encodings:
            for encoding in face_encodings:
                FaceEncoding.objects.create(
                    photo=photo,
                    encoding=np.array(encoding).tobytes()
                )
            photo.is_processed = True
            photo.save()
            return f"Photo {photo_id} processed successfully"
        else:
            return f"No face found in photo {photo_id}"

    except Photo.DoesNotExist:
        return f"Photo {photo_id} not found"
    except Exception as e:
        logger.error(f"Error processing photo {photo_id}: {str(e)}")
        return f"Error processing photo {photo_id}: {str(e)}"









# from celery import shared_task
# import face_recognition
# import numpy as np
# from PIL import Image

# @shared_task
# def process_photo(photo_id):
#     from .models import Photo, FaceEncoding
    
#     try:
#         photo = Photo.objects.get(id=photo_id)
#         image = face_recognition.load_image_file(photo.image.path)
#         face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2)
#         face_encodings = face_recognition.face_encodings(image, face_locations)
        
#         if face_encodings:
#             for encoding in face_encodings:
#                 FaceEncoding.objects.create(
#                     photo=photo, 
#                     encoding=np.array(encoding).tobytes()
#                 )
#             return f"Photo {photo_id} processed successfully"
#         return f"No face found in photo {photo_id}"
    
#     except Photo.DoesNotExist:
#         return f"Photo {photo_id} not found"
#     except Exception as e:
#         return f"Error processing photo {photo_id}: {str(e)}"
