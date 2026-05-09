from pillow_heif import register_heif_opener
import pillow_avif  # registers AVIF opener automatically
from PIL import Image, ImageOps
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from io import BytesIO
import os
import logging
register_heif_opener()

CONVERT_TO_JPEG_FORMATS = {".heic", ".heif", ".avif"}

logger = logging.getLogger(__name__)

def convert_original_to_jpeg_if_needed(photo):
    image_name = photo.image.name
    _, ext = os.path.splitext(image_name)

    if ext.lower() not in CONVERT_TO_JPEG_FORMATS:
        return

    logger.info(f"Converting {ext} → JPEG for photo {photo.id}")

    try:
        with default_storage.open(image_name, "rb") as f:
            img = Image.open(f)

            # Fix orientation (critical for iPhone photos)
            img = ImageOps.exif_transpose(img)

            # Handle transparency (AVIF edge case)
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert("RGB")

        new_image_name = os.path.splitext(image_name)[0] + ".jpg"

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=95, optimize=True)
        buffer.seek(0)

        default_storage.save(new_image_name, ContentFile(buffer.read()))
        default_storage.delete(image_name)

        photo.image.name = new_image_name
        photo.save(update_fields=["image"])

        logger.info(f"Saved as JPEG: {new_image_name}")

    except Exception as e:
        logger.exception(f"Conversion failed for photo {photo.id}: {e}")