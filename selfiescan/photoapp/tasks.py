# tasks.py (modified)
from celery import shared_task
import face_recognition
import numpy as np
from PIL import Image, ImageOps
import logging
import cv2
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from io import BytesIO

logger = logging.getLogger(__name__)

# Initialize Rekognition client (singleton for efficiency)
rekognition = boto3.client(
    'rekognition',
    region_name= 'ap-south-1',  # e.g., 'us-east-1' from settings.py
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

def get_or_create_collection(event_id):
    """Create a Rekognition collection for the event if it doesn't exist."""
    collection_id = f"event_{event_id}"
    try:
        # Check if collection exists
        rekognition.describe_collection(CollectionId=collection_id)
        logger.info(f"Collection {collection_id} already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            try:
                rekognition.create_collection(CollectionId=collection_id)
                logger.info(f"Created new collection: {collection_id}")
            except ClientError as create_error:
                logger.error(f"Failed to create collection {collection_id}: {create_error}")
                raise
        else:
            logger.error(f"Error checking collection {collection_id}: {e}")
            raise
    return collection_id

def load_and_correct_image(file_obj, max_side=2000):
    try:
        img = Image.open(file_obj).convert("RGB")
        img = ImageOps.exif_transpose(img)
        
        if max(img.size) > max_side:
            img.thumbnail((max_side,max_side), Image.LANCZOS)
        # Convert to OpenCV format for fallback
        image_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return image_cv
    except Exception as e:
        logger.error(f"[ERROR] Failed to process image: {e}")
        return None

def resize_image_for_processing(image, max_side=1600):
    h, w = image.shape[:2]
    scale = max_side / max(h, w)

    if scale < 1:
        image = cv2.resize(
            image,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA
        )
    return image

def load_resize_for_rekognition(file_obj, max_side=4000):
    img = Image.open(file_obj).convert("RGB")
    img = ImageOps.exif_transpose(img)

    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)

    buffer = BytesIO()
    img.save("debug_pil.jpg", format="JPEG", quality=95)
    img.save(buffer, format="JPEG", quality=95)
    
    return buffer.getvalue()


        
        
# face encoding of uploaded photos (Rekognition + fallback)
@shared_task(bind=True,acks_late=True,autoretry_for=(Exception,),retry_backoff=True,retry_jitter=True)
def process_photo(self, photo_id):
    from .models import Photo, FaceEncoding

    try:
        photo = Photo.objects.get(id=photo_id)
        image_name = photo.image.name
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        if photo.is_processed:
            return f"Photo {photo_id} already processed"

        if FaceEncoding.objects.filter(photo=photo).exists():
            photo.is_processed = True
            photo.save(update_fields=["is_processed"])
            return f"Encodings already exist for photo {photo_id}"

        collection_id = get_or_create_collection(photo.event.event_id)
        index_response = None

        # --------------------
        # Try Rekognition
        # --------------------
        try:
            index_response = rekognition.index_faces(
                CollectionId="INVALID_COLLECTION",
                Image={'S3Object': {'Bucket': bucket, 'Name': image_name}},
                ExternalImageId=str(photo.id)
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code in ("InvalidImageFormatException", "ValidationException"):
                logger.warning(
                    f"S3Object failed ({error_code}) for {photo_id}, "
                    f"retrying with resized bytes"
                )

                with default_storage.open(image_name, 'rb') as f:
                    image_bytes = load_resize_for_rekognition(f, max_side=4000)

                index_response = rekognition.index_faces(
                    CollectionId=collection_id,
                    Image={'Bytes': image_bytes},
                    ExternalImageId=str(photo.id)
                )

            else:
                # AWS outage / permissions / throttling → fallback
                logger.warning(
                    f"Rekognition failed for {photo_id} ({error_code}), "
                    f"falling back to face_recognition"
                )
                index_response = None

        # --------------------
        # Rekognition success path
        # --------------------
        if index_response:
            face_records = index_response.get("FaceRecords", [])
            face_count = len(face_records)

            logger.info(f"Rekognition indexed {face_count} faces for {photo_id}")

            photo.is_processed = True
            photo.save()

            return f"Photo {photo_id} processed with Rekognition: {face_count} faces"

      
        # Fallback: face_recognition
       
        logger.info(f"Using fallback face_recognition for photo {photo_id}")

        with default_storage.open(image_name, 'rb') as f:
            image = load_and_correct_image(f)

        if image is None:
            photo.is_processed = True
            photo.save()
            return f"Failed to load image for photo {photo_id}"

        image = resize_image_for_processing(image)
        face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1)

        if not face_locations:
            photo.is_processed = True
            photo.save()
            return f"No faces found (fallback) for photo {photo_id}"

        for loc in face_locations:
            encoding = face_recognition.face_encodings(image, [loc])[0]
            FaceEncoding.objects.create(
                photo=photo,
                encoding=np.array(encoding).tobytes()
            )

        photo.is_processed = True
        photo.save()

        return f"Photo {photo_id} processed with fallback: {len(face_locations)} faces"

    except Photo.DoesNotExist:
        return f"Photo {photo_id} not found"

    except Exception as e:
        logger.error(f"Fatal error processing photo {photo_id}: {e}")
        raise self.retry(exc=e)

# This task is for re-running pending processing of the photos of the event 
@shared_task
def process_event_photos(event_id):
    from .models import Photo
    photos = Photo.objects.filter(event_id=event_id)

    for photo in photos:
        process_photo.delay(photo.id)
 
# following is the working tasks exclusively for the face_recognition/implemented before aws reko.     
# from celery import shared_task
# import face_recognition
# import numpy as np
# from PIL import Image, ImageOps
# import logging
# import cv2
# from django.core.files.base import ContentFile
# from django.core.files.storage import default_storage

# logger = logging.getLogger(__name__)


# def load_and_correct_image(file_obj):
#     try:
#         image_pil = Image.open(file_obj)

#         exif = image_pil.getexif()
#         original_orientation = exif.get(0x0112, 1)
        

#         image_pil = ImageOps.exif_transpose(image_pil)
#         new_exif = image_pil.getexif()
#         new_orientation = new_exif.get(0x0112, 1)
        

#         # Convert to OpenCV format
#         image_cv = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

#         return image_cv

#     except Exception as e:
#         print(f"[ERROR] Failed to process image {image_path}: {e}")
#         return None




# def resize_image_for_processing(image, max_width=600):
#     height, width = image.shape[:2]
#     if width > max_width:
#         scaling_factor = max_width / width
#         new_size = (int(width * scaling_factor), int(height * scaling_factor))
#         image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
#     return image

# # face encoding of uploaded photos
# @shared_task(bind=True, acks_late=True, autoretry_for=(Exception,), retry_backoff=True,retry_jitter=True)
# def process_photo(self, photo_id):
#     from .models import Photo, FaceEncoding

#     try:
#         photo = Photo.objects.get(id=photo_id)
#         image_name = photo.image.name  # relative path
#         with default_storage.open(image_name, 'rb') as f:
#             image = load_and_correct_image(f)

#         if image is None:
#             return f"Failed to load image for photo {photo_id}"
#         # Skip if already processed
#         if photo.is_processed:
#             return f"Photo {photo_id} already processed"

#         # Skip if encodings already exist (prevent duplicates)
#         if FaceEncoding.objects.filter(photo=photo).exists():
#             if not photo.is_processed:
#                 photo.is_processed = True
#                 photo.save(update_fields=["is_processed"]) # or photo.save()
#             return f"Encodings for photo {photo_id} already exist"


#         image = resize_image_for_processing(image)

#         face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1)
#         logger.info(f"Detected {len(face_locations)} face locations")
        
#         if not face_locations:
#             logger.warning(f"No faces detected in {image_name}. Marking as processed.")
#             photo.is_processed = True
#             photo.save()
#             return f"No face found in photo {photo_id}"

        
#         face_encodings = []
#         for idx, location in enumerate(face_locations):
#             encoding = face_recognition.face_encodings(image, [location])[0]
#             face_encodings.append(encoding)
            

#         # Draw boxes on the image for verification
#         # draw = ImageDraw.Draw(pil_image)
#         # for (top, right, bottom, left) in face_locations:
#         #     draw.rectangle([left, top, right, bottom], outline="red", width=2)
        
#         # Save the annotated image
#         # annotated_path = os.path.join(os.path.dirname(image_path), f"annotated_{os.path.basename(image_path)}")
#         # pil_image.save(annotated_path)
#         # logger.info(f"Annotated image saved at {annotated_path}")

        
#         if face_encodings:
#             for encoding in face_encodings:
#                 FaceEncoding.objects.create(
#                     photo=photo,
#                     encoding=np.array(encoding).tobytes()
#                 )
             
#             photo.is_processed = True
#             photo.save()
#             return f"Photo {photo_id} processed successfully"
#         else:
#             photo.is_processed = True
#             photo.save()
#             return f"No face found in fallback for photo {photo_id}"

#     except Photo.DoesNotExist:
#         return f"Photo {photo_id} not found"
#     except Exception as e:
#         logger.error(f"Error processing photo {photo_id}: {str(e)}")
#         raise self.retry(exc=e)




  

from celery import shared_task
from django.core.files.base import ContentFile

import logging
from PIL import Image, ImageDraw, ImageFont
import io
import os

logger = logging.getLogger(__name__)

# Use a system font that’s commonly available (e.g., DejaVuSans on Linux)
SYSTEM_FONT_PATH = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"  # Common on Linux servers

def load_font(size):
    """Load a system font with the specified size, fallback to default if unavailable."""
    try:
        if not os.path.exists(SYSTEM_FONT_PATH):
            logger.warning(f"System font not found at {SYSTEM_FONT_PATH}, falling back to default font")
            return ImageFont.load_default()
        font = ImageFont.truetype(SYSTEM_FONT_PATH, size=size)
        logger.info(f"Loaded system font from {SYSTEM_FONT_PATH} with size {size}")
        return font
    except Exception as e:
        logger.error(f"Failed to load system font: {e}, falling back to default font")
        return ImageFont.load_default()

@shared_task(bind=True, acks_late=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def branded_photo(self, photo_id):
    try:
        from .models import Photo
        photo = Photo.objects.get(id=photo_id)
        event = photo.event

        if not event.branding_enabled:
            logger.info(f"Branding not enabled for event {event.id}. Skipping branding for photo {photo_id}.")
            return f"Branding not enabled for photo {photo_id}"

        if not photo.is_processed:
            logger.warning(f"Photo {photo_id} not yet processed. Skipping branding.")
            return f"Photo {photo_id} not processed"

        if photo.is_branded:
            logger.info(f"Photo {photo_id} already branded.")
            return f"Photo {photo_id} already branded"

        # Open the image with PIL and convert to RGBA
        image_name = photo.image.name
        with default_storage.open(image_name, 'rb') as f:
            image = Image.open(f).convert("RGBA")

        if image is None:
            logger.error(f"Failed to load image for branding photo {photo_id}")
            return f"Failed to load image for branding photo {photo_id}"

        logger.info(f"Image loaded: size={image.size}, mode={image.mode}")
        width, height = image.size
        margin = 30  # Margin from edges in pixels

        # Apply branding
        right_margin = 30  # Margin from right edge in pixels
        bottom_margin = 15  # Reduced margin from bottom edge in pixels

        if event.branding_image and event.branding_image.name:
            # Load and scale the logo
            with default_storage.open(event.branding_image.name, 'rb') as logo_file:
                logo = Image.open(logo_file).convert("RGBA")
            has_alpha = logo.getchannel('A').getextrema() != (255, 255)
            logger.info(f"Logo loaded: size={logo.size}, mode={logo.mode}, has_alpha={has_alpha}")
            
            if not has_alpha:
                logger.warning(f"Logo for event {event.id} has no transparency. Please ensure the logo has a transparent background.")

            # Determine if the logo is wide (e.g., a text logo)
            logo_aspect = logo.width / logo.height
            is_wide_logo = logo_aspect > 2  # Consider it wide if width/height > 2
            logger.info(f"Logo aspect ratio: {logo_aspect}, is_wide_logo={is_wide_logo}")

            if is_wide_logo:
                # Scale based on height for better readability of text logos
                logo_max_height = min(int(height * 0.1), 100)  # 10% of image height, max 100px
                logo_height = logo_max_height
                logo_width = int(logo_height * logo_aspect)
                # Ensure the width doesn't exceed 50% of the image width or 600px
                max_allowed_width = min(int(width * 0.5), 600)
                if logo_width > max_allowed_width:
                    logo_width = max_allowed_width
                    logo_height = int(logo_width / logo_aspect)
                logger.info(f"Scaling wide logo by height: new_size=({logo_width}, {logo_height})")
            else:
                # Scale based on width for compact logos
                logo_max_width = min(int(width * 0.15), 300)  # 15% of image width, max 300px
                logo_width = logo_max_width
                logo_height = int(logo_width / logo_aspect)
                logger.info(f"Scaling compact logo by width: new_size=({logo_width}, {logo_height})")

            # Ensure the logo fits within the image (accounting for right margin)
            if logo_width > (width - right_margin):
                logo_width = width - right_margin
                logo_height = int(logo_width / logo_aspect)
                logger.info(f"Adjusted logo to fit within image: new_size=({logo_width}, {logo_height})")

            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # Position logo in bottom-right corner with separate margins
            logo_position = (width - logo_width - right_margin, height - logo_height - bottom_margin)
            image.paste(logo, logo_position, logo)  # Use alpha channel for transparency
            logger.info(f"Logo pasted at position={logo_position}")

        elif event.branding_text:
            # Load font with calculated size
            font_size = max(min(int(width * 0.025), 80), 20)  # 2.5% of width, capped between 20px and 60px
            logger.info(f"calculated font size - {font_size}")
            
           
            font = load_font(font_size)

            text = event.branding_text
            # Create a temporary draw object to calculate text size
            temp_image = Image.new("RGBA", (1, 1))
            temp_draw = ImageDraw.Draw(temp_image)
            text_bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            logger.info(f"Text dimensions: width={text_width}, height={text_height}")

            # Position text in bottom-right corner
            text_x = width - text_width - margin
            text_y = height - text_height - margin
            rect_x1, rect_y1 = text_x - 10, text_y - 10
            rect_x2, rect_y2 = text_x + text_width + 10, text_y + text_height + 10
            logger.info(f"Text position: x={text_x}, y={text_y}, rect=({rect_x1},{rect_y1})-({rect_x2},{rect_y2})")

            # Draw semi-transparent background and text on an overlay
            overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            # Draw semi-transparent background rectangle
            overlay_draw.rectangle(
                (rect_x1, rect_y1, rect_x2, rect_y2),
                fill=(0, 0, 0, 128)  # Black with 50% opacity
            )

            # Draw text shadow on the overlay
            shadow_offset = 2
            overlay_draw.text(
                (text_x + shadow_offset, text_y + shadow_offset),
                text,
                font=font,
                fill=(0, 0, 0, 200)  # Dark shadow with slight transparency
            )

            # Draw main text on the overlay
            overlay_draw.text(
                (text_x, text_y),
                text,
                font=font,
                fill=(235, 235, 235, 255)  # Light gray text
            )

            # Composite the overlay onto the main image
            image = Image.composite(overlay, image, overlay)
            logger.info(f"Overlay applied: mode={overlay.mode}, size={overlay.size}")

        # Convert back to RGB for saving as JPEG
        image = image.convert("RGB")

        # Save the branded image
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        branded_file = ContentFile(buffer.getvalue())

        filename = f"{photo_id}_branded.jpg"
        photo.branded_image.save(filename, branded_file, save=False)
        photo.is_branded = True
        photo.save(update_fields=["branded_image", "is_branded"])
        logger.info(f"Photo {photo_id} branded and saved successfully")
        return f"Photo {photo_id} branded successfully"

    except Photo.DoesNotExist:
        logger.error(f"Photo {photo_id} not found")
        return f"Photo {photo_id} not found"
    except Exception as e:
        logger.error(f"Error branding photo {photo_id}: {str(e)}")
        raise self.retry(exc=e)

# e-mail notification for expired subscription and welcome email

from django.core.mail import EmailMultiAlternatives
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
    "renew_link": "https://photoflow.in/billing/",
    "unsubscribe_link": f"https://photoflow.in/unsubscribe/{user.id}/",
    "year": timezone.now().year,
})
        email = EmailMultiAlternatives(
        subject="Reminder: Your Subscription has Expired",
        body="This is an HTML-only email. Please view it in an HTML-compatible client.",
        from_email="noreply@photoflow.in",
        to=[user.email],
)
        email.attach_alternative(html_message, "text/html")
        email.send()
        print("email sent")
        sub.last_notified = now
        sub.save(update_fields=["last_notified"])




@shared_task
def send_welcome_email_task(user_id, email):
    subject = "Welcome to PhotoFlow 🎉"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [email]

    # Render HTML template
    html_content = render_to_string("emails/welcome_email.html", {
        "user_id": user_id,
    })

    # Plain text fallback
    text_content = "Welcome to PhotoFlow! We're glad to have you here."

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
