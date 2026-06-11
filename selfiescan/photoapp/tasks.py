from celery import shared_task
import face_recognition
from humanfriendly import text
import numpy as np
from PIL import Image, ImageOps
import logging,os
import cv2
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import boto3
from botocore.exceptions import ClientError, NoCredentialsError,EndpointConnectionError
from qrcode import image
from rest_framework import response
import mysite.settings as settings
from io import BytesIO
from .utils.image_variants import generate_variant, VARIANTS
from .utils.convert_to_jpeg import convert_original_to_jpeg_if_needed
logger = logging.getLogger(__name__)

# Initialize Rekognition client (singleton for efficiency)
rekognition = boto3.client(
    'rekognition',
    region_name= 'ap-south-1',
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
    #img.save("debug_pil.jpg", format="JPEG", quality=95)
    img.save(buffer, format="JPEG", quality=95)
    
    return buffer.getvalue()

def generate_photo_variants(photo):

    if photo.thumb_image and photo.medium_image and photo.large_image:
        return
    image_field = photo.image
    original_size_bytes = image_field.size

    image_field_map = {
        "thumb": photo.thumb_image,
        "medium": photo.medium_image,
        "large": photo.large_image,
    }

    base_name = os.path.basename(photo.image.name)
    name, _ = os.path.splitext(base_name)

    for variant, field in image_field_map.items():
        config = VARIANTS[variant]

        buffer = generate_variant(
            photo.image,
            size=config["size"],
            quality=config["quality"],
            original_size_bytes=original_size_bytes,
            is_large=(variant == "large")
        )

        if not buffer:
            continue

        filename = f"{name}_{variant}.jpg"

        field.save(
            filename,
            ContentFile(buffer.read()),
            save=False
        )

    photo.save(update_fields=["thumb_image", "medium_image", "large_image"])


def trigger_branding_if_enabled(photo):
    """Trigger branded_photo task if event has branding enabled."""
    if photo.event.branding_enabled and not photo.is_branded:
        branded_photo.delay(photo.id)      
        
# face encoding of uploaded photos (Rekognition + fallback)
@shared_task(bind=True,acks_late=True,autoretry_for=(ClientError, EndpointConnectionError),retry_backoff=True,retry_jitter=True,retry_kwargs={"max_retries": 3})
def process_photo(self, photo_id):
    from .models import Photo, FaceEncoding

    try:
        photo = Photo.objects.get(id=photo_id)
        
        if photo.is_processed:
            return f"Photo {photo_id} already processed"
        
        _, ext = os.path.splitext(photo.image.name)
        if ext.lower() in {".heic", ".heif", ".avif"}:
            convert_original_to_jpeg_if_needed(photo)
            photo.refresh_from_db()
        
        image_name = photo.image.name
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        

        if FaceEncoding.objects.filter(photo=photo).exists():
            photo.is_processed = True
            photo.save(update_fields=["is_processed"])
            trigger_branding_if_enabled(photo)
            return f"Encodings already exist for photo {photo_id}"

        collection_id = get_or_create_collection(photo.event.event_id)
        index_response = None

        # --------------------
        # Try Rekognition
        # --------------------
        try:
            index_response = rekognition.index_faces(
                CollectionId=collection_id,
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
        if index_response and "FaceRecords" in index_response:
            face_records = index_response.get("FaceRecords", [])
            face_count = len(face_records)

            logger.info(f"Rekognition indexed {face_count} faces for {photo_id}")
            generate_photo_variants(photo)
            photo.is_processed = True
            photo.save(update_fields=["is_processed"])
            trigger_branding_if_enabled(photo)

            return f"Photo {photo_id} processed with Rekognition: {face_count} faces"

      
        # Fallback: face_recognition
       
        logger.info(f"Using fallback face_recognition for photo {photo_id}")

        with default_storage.open(image_name, 'rb') as f:
            image = load_and_correct_image(f)

        if image is None:
            photo.is_processed = True
            photo.save()
            trigger_branding_if_enabled(photo)
            return f"Failed to load image for photo {photo_id}"

        image = resize_image_for_processing(image)
        face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1)

        if not face_locations:
            photo.is_processed = True
            photo.save()
            trigger_branding_if_enabled(photo)
            return f"No faces found (fallback) for photo {photo_id}"

        for loc in face_locations:
            encoding = face_recognition.face_encodings(image, [loc])[0]
            FaceEncoding.objects.create(
                photo=photo,
                encoding=np.array(encoding).tobytes()
            )
        generate_photo_variants(photo)
        photo.is_processed = True
        photo.save(update_fields=["is_processed"])
        trigger_branding_if_enabled(photo)

        return f"Photo {photo_id} processed with fallback: {len(face_locations)} faces"

    except Photo.DoesNotExist as e:
        raise self.retry(exc=e, countdown=2)

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
 

  
# Apply branding (logo or text) to photos marked for customer selection
from celery import shared_task
from django.core.files.base import ContentFile

import logging
from PIL import Image, ImageDraw, ImageFont
import io
import os

logger = logging.getLogger(__name__)


FONT_DIR = os.path.join(settings.BASE_DIR, "static", "fonts")

BRAND_FONTS = {
    "elegant":  os.path.join(FONT_DIR, "Cormorant-SemiBold.ttf"), 
    "modern":   os.path.join(FONT_DIR, "Montserrat-Medium.ttf"), 
    "classic":  os.path.join(FONT_DIR, "PlayfairDisplay-Regular.ttf"),
    "stylish":  os.path.join(FONT_DIR, "Rancho-Regular.ttf"),
    "luxury":  os.path.join(FONT_DIR, "Cinzel-Medium.ttf"),  
    "handwritten": os.path.join(FONT_DIR, "PlaywriteGBSGuides-Italic.ttf"),
    "ultra_modern": os.path.join(FONT_DIR, "ZenTokyoZoo-Regular.ttf"),   
}

def load_font(size, style="modern"):
    path = BRAND_FONTS.get(style, BRAND_FONTS["modern"])
    try:
        return ImageFont.truetype(path, size=size)
    except Exception:
        return ImageFont.load_default()
    
def apply_logo_premium(image, logo, position, opacity=220):
    """Paste logo with configurable opacity and a subtle drop shadow."""
    # Adjust logo opacity
    r, g, b, a = logo.split()
    a = a.point(lambda x: int(x * opacity / 255))
    logo = Image.merge("RGBA", (r, g, b, a))

    # Drop shadow: a blurred dark version offset by a few pixels
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_logo = Image.new("RGBA", logo.size, (0, 0, 0, 160))
    shadow_logo.putalpha(a)  # same shape as logo
    shadow_offset = (position[0] + 3, position[1] + 3)
    shadow.paste(shadow_logo, shadow_offset, shadow_logo)

    # Apply gaussian blur to shadow
    from PIL import ImageFilter
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))

    # Composite: shadow first, then logo
    image = Image.alpha_composite(image, shadow)
    image.paste(logo, position, logo)
    return image

def compute_position(event, element_w, element_h, img_w, img_h, margin=30):
    pos = getattr(event, "branding_position", "bottom_right")
    positions = {
        "bottom_right":  (img_w - element_w - margin, img_h - element_h - margin),
        "bottom_left":   (margin, img_h - element_h - margin),
        "bottom_center": ((img_w - element_w) // 2, img_h - element_h - margin),
        "top_right":     (img_w - element_w - margin, margin),
    }
    return positions.get(pos, positions["bottom_right"])


def apply_text_premium(image, text, font, position, text_color=(255, 255, 255, 150)):
    """Text with frosted-glass background, properly vertically centered."""
    tx, ty = position
    temp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(temp)
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bbox_top_offset = bbox[1]

    pad_x, pad_y = 18, 10
    pill_w = tw + pad_x * 2
    pill_h = th + pad_y * 2

    # Frosted glass background
    region_box = (tx - pad_x, ty - pad_y, tx - pad_x + pill_w, ty - pad_y + pill_h)
    region = image.crop(region_box).convert("RGBA")
    from PIL import ImageFilter, ImageEnhance
    blurred = region.filter(ImageFilter.GaussianBlur(radius=12))
    darkened = ImageEnhance.Brightness(blurred).enhance(0.75)
    overlay = Image.new("RGBA", darkened.size, (0, 0, 0, 40))
    frosted = Image.alpha_composite(darkened, overlay)
    image.paste(frosted, (region_box[0], region_box[1]))

    # Vertically center text
    center_y = (ty - pad_y + ty - pad_y + pill_h) // 2
    text_y = center_y - th // 2 - bbox_top_offset

    # Shadow layer via alpha_composite — respects opacity
    

    # Text layer via alpha_composite — respects opacity
    text_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(text_layer).text((tx, text_y), text, font=font, fill=text_color)
    image = Image.alpha_composite(image, text_layer)

    return image

def apply_text_plain(image, text, font, position, text_color=(255, 255, 255, 80)):
    tx, ty = position
    temp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(temp)
    bbox = d.textbbox((0, 0), text, font=font)
    th = bbox[3] - bbox[1]
    text_y = ty - th // 2 - bbox[1]

    from PIL import ImageFilter

    # Shadow layer — draw text first, THEN blur
    
    # Text layer — alpha_composite properly blends opacity
    text_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(text_layer).text((tx, text_y), text, font=font, fill=text_color)
    image = Image.alpha_composite(image, text_layer)

    return image

def apply_text_diagonal(image, text, font, opacity=150, num_lines=3):
    """
    Draw repeated diagonal watermark text similar to the frontend canvas preview.
    """
    import math
    from PIL import Image, ImageDraw, ImageFont

    width, height = image.size

    # Match frontend diagonal angle
    angle = math.degrees(math.atan2(height, width))

    # Measure text
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Match frontend spacing
    spacing_x = text_width + 80
    spacing_y = text_height + 60

    # Work on a larger square so rotation doesn't clip
    diagonal = int(math.sqrt(width**2 + height**2))
    canvas_size = diagonal * 2

    watermark = Image.new(
        "RGBA",
        (canvas_size, canvas_size),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(watermark)

    center_x = canvas_size // 2
    center_y = canvas_size // 2

    start_y = -(diagonal / 2)
    line_gap = diagonal / (num_lines + 1)

    # Draw exactly like frontend
    for row in range(num_lines):
        y = start_y + line_gap * (row + 1)

        # Stagger every second row
        x_offset = spacing_x / 2 if row % 2 else 0

        x = -diagonal
        while x < diagonal:
            draw.text(
                (
                    center_x + x + x_offset,
                    center_y + y
                ),
                text,
                font=font,
                fill=(255, 255, 255, opacity),
            )
            x += spacing_x

    # Rotate to image diagonal
    watermark = watermark.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=False,
    )

    # Crop center region back to image size
    left = (canvas_size - width) // 2
    top = (canvas_size - height) // 2

    watermark = watermark.crop(
        (
            left,
            top,
            left + width,
            top + height,
        )
    )

    result = image.convert("RGBA")
    result = Image.alpha_composite(result, watermark)

    return result

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

        image_name = photo.large_image.name or photo.image.name
        with default_storage.open(image_name, 'rb') as f:
            image = Image.open(f)
            exif = image.getexif()
            image = image.convert("RGBA")

        if image is None:
            logger.error(f"Failed to load image for branding photo {photo_id}")
            return f"Failed to load image for branding photo {photo_id}"

        logger.info(f"Image loaded: size={image.size}, mode={image.mode}")
        width, height = image.size
        right_margin = 30
        margin = 30

        if event.branding_image and event.branding_image.name:
            with default_storage.open(event.branding_image.name, 'rb') as logo_file:
                logo = Image.open(logo_file).convert("RGBA")
            has_alpha = logo.getchannel('A').getextrema() != (255, 255)
            logger.info(f"Logo loaded: size={logo.size}, mode={logo.mode}, has_alpha={has_alpha}")

            if not has_alpha:
                logger.warning(f"Logo for event {event.id} has no transparency.")

            logo_aspect = logo.width / logo.height
            is_wide_logo = logo_aspect > 2
            logger.info(f"Logo aspect ratio: {logo_aspect}, is_wide_logo={is_wide_logo}")

            if is_wide_logo:
                logo_max_height = min(int(height * 0.1), 100)
                logo_height = logo_max_height
                logo_width = int(logo_height * logo_aspect)
                max_allowed_width = min(int(width * 0.5), 600)
                if logo_width > max_allowed_width:
                    logo_width = max_allowed_width
                    logo_height = int(logo_width / logo_aspect)
                logger.info(f"Scaling wide logo by height: new_size=({logo_width}, {logo_height})")
            else:
                logo_max_width = min(int(width * 0.15), 300)
                logo_width = logo_max_width
                logo_height = int(logo_width / logo_aspect)
                logger.info(f"Scaling compact logo by width: new_size=({logo_width}, {logo_height})")

            if logo_width > (width - right_margin):
                logo_width = width - right_margin
                logo_height = int(logo_width / logo_aspect)
                logger.info(f"Adjusted logo to fit within image: new_size=({logo_width}, {logo_height})")

            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            logo_position = compute_position(event, logo_width, logo_height, width, height, margin=margin)
            opacity_255 = int(event.branding_opacity * 255 / 100)
            image = apply_logo_premium(image, logo, logo_position, opacity=opacity_255)
            logger.info(f"Logo pasted at position={logo_position}")

        elif event.branding_text:
            text = event.branding_text.strip()
            font_size = max(min(int(width * 0.025), 80), 20)
            font = load_font(size=font_size, style=event.branding_font)

            temp = Image.new("RGBA", (1, 1))
            bbox = ImageDraw.Draw(temp).textbbox((0, 0), text, font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            text_position = compute_position(event, text_w, text_h, width, height, margin=margin)

            text_style = getattr(event, "branding_text_style", "box")

            if text_style == "plain":
                alpha = int(event.branding_opacity * 255 / 100)
                image = apply_text_plain(image, text, font, text_position, text_color=(255, 255, 255, alpha))
            elif text_style == "diagonal":
                alpha = int(event.branding_opacity * 255 / 100)
                image = apply_text_diagonal(image, text, font, opacity=alpha, num_lines=3)
            else:
                alpha = int(event.branding_opacity * 255 / 100)
                image = apply_text_premium(image, text, font, text_position, text_color=(255, 255, 255, alpha))
                
        image = image.convert("RGB")
        buffer = io.BytesIO()
        
        exif = image.getexif()
        
        exif[0x010E] = f"Event: {event.name}"                          # ImageDescription
        exif[0x013B] = event.studio_name or event.photographer.get_full_name()  # Artist
        exif[0x8298] = event.photographer.get_full_name() if event.photographer else event.studio_name    # Copyright
        exif[0x0131] = f"photoflow.in"          # Software
        image.save(buffer, format="JPEG", quality=97, subsampling=0, exif=exif.tobytes())
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
