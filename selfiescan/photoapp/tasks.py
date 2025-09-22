from celery import shared_task
import face_recognition
import numpy as np
from PIL import Image, ImageOps
import logging
import cv2
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def load_and_correct_image(file_obj):
    try:
        image_pil = Image.open(file_obj)

        exif = image_pil.getexif()
        original_orientation = exif.get(0x0112, 1)
        

        image_pil = ImageOps.exif_transpose(image_pil)
        new_exif = image_pil.getexif()
        new_orientation = new_exif.get(0x0112, 1)
        

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

# face encoding of uploaded photos
@shared_task(bind=True, acks_late=True, autoretry_for=(Exception,), retry_backoff=True,retry_jitter=True)
def process_photo(self, photo_id):
    from .models import Photo, FaceEncoding

    try:
        photo = Photo.objects.get(id=photo_id)
        image_name = photo.image.name  # relative path
        with default_storage.open(image_name, 'rb') as f:
            image = load_and_correct_image(f)

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
        logger.info(f"Detected {len(face_locations)} face locations")
        
        if not face_locations:
            logger.warning(f"No faces detected in {image_name}. Marking as processed.")
            photo.is_processed = True
            photo.save()
            return f"No face found in photo {photo_id}"

        
        face_encodings = []
        for idx, location in enumerate(face_locations):
            encoding = face_recognition.face_encodings(image, [location])[0]
            face_encodings.append(encoding)
            

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
        with default_storage.open(photo.image.name, 'rb') as f:
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

        if event.branding_image and event.branding_image.path:
            # Load and scale the logo
            logo = Image.open(event.branding_image.path).convert("RGBA")
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

# e-mail notification for expired subscription

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
