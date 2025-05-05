from celery import shared_task
import face_recognition
import numpy as np
from PIL import Image, ImageOps
import logging
import cv2

logger = logging.getLogger(__name__)


def load_and_correct_image(image_path):
    try:
        image_pil = Image.open(image_path)

        exif = image_pil.getexif()
        original_orientation = exif.get(0x0112, 1)
        print(f"[DEBUG] Original orientation of {image_path}: {original_orientation}")

        image_pil = ImageOps.exif_transpose(image_pil)
        new_exif = image_pil.getexif()
        new_orientation = new_exif.get(0x0112, 1)
        print(f"[DEBUG] New Orientation of {image_path} is {new_orientation}")

        # Convert to OpenCV format
        image_cv = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

        return image_cv

    except Exception as e:
        print(f"[ERROR] Failed to process image {image_path}: {e}")
        return None




def resize_image_for_processing(image, max_width=800):
    height, width = image.shape[:2]
    if width > max_width:
        scaling_factor = max_width / width
        new_size = (int(width * scaling_factor), int(height * scaling_factor))
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    return image


@shared_task(bind=True, acks_late=True, autoretry_for=(Exception,), retry_backoff=True,retry_jitter=True)
def process_photo(self, photo_id):
    from .models import Photo, FaceEncoding
    
    try:
        photo = Photo.objects.get(id=photo_id)
        image_path = photo.image.path
        image = load_and_correct_image(image_path)
               

        if image is None:
            return f"Failed to load image for photo {photo_id}"
        # Skip if already processed
        if photo.is_processed:
            return f"Photo {photo_id} already processed"

        # Skip if encodings already exist (prevent duplicates)
        if FaceEncoding.objects.filter(photo=photo).exists():
            if not photo.is_processed:
                photo.is_processed = True
                photo.save(update_fields=["is_processed"]) # or photo.save()
            return f"Encodings for photo {photo_id} already exist"


        image = resize_image_for_processing(image)

        face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=3)
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
        raise self.retry(exc=e)



# e-mail notification exoired subscription

from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string

@shared_task
def notify_expired_subscriptions():
    from .models import Subscription
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q

    now = timezone.now()
    fifteen_days_ago = now - timedelta(days=15)

    expired_subs = Subscription.objects.filter(
        Q(last_notified__lt=fifteen_days_ago) | Q(last_notified__isnull=True),
        end_date__lt=now,
        unsubscribed=False,
        subscription_type__in=['MONTHLY', 'YEARLY'],
    )

    for sub in expired_subs:
        user = sub.photographer

        html_message = render_to_string("emails/subscription_expired.html", {
    "username": user.username,
    "plan_type": sub.subscription_type.title(),
    "end_date": sub.end_date.date(),
    "renew_link": "http://127.0.0.1:8000/billing/",
    "unsubscribe_link": f"http://127.0.0.1:8000/unsubscribe/{user.id}/",
    "year": timezone.now().year,
})
        email = EmailMultiAlternatives(
        subject="Reminder: Your Subscription has Expired",
        body="This is an HTML-only email. Please view it in an HTML-compatible client.",
        from_email="noreply@selfiescan.com",
        to=[user.email],
)
        email.attach_alternative(html_message, "text/html")
        email.send()
        print("email sent")
        sub.last_notified = now
        sub.save(update_fields=["last_notified"])
