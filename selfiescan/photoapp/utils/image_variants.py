from PIL import Image, ImageOps
from io import BytesIO

VARIANTS = {
    "thumb":  {"size": (600, 600),   "quality": 70},
    "medium": {"size": (1600, 1600), "quality": 80},
    "large":  {"size": (3500, 3500), "quality": 95},
}

# Large variant threshold
LARGE_SKIP_MAX_BYTES = 1.5 * 1024 * 1024  
LARGE_SKIP_MAX_DIM   = 1600              


def generate_variant(image_field, size, quality, original_size_bytes, is_large=False):
    with image_field.open("rb") as f:
        img = Image.open(f)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")

        original_width, original_height = img.size

        # Skip upscale
        if original_width <= size[0] and original_height <= size[1]:
            # For large variant → skip completely
            if is_large:
                return None
            # For others → just keep original size
            resized_img = img
        else:
            resized_img = ImageOps.contain(img, size)

        buffer = BytesIO()

        resized_img.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True
        )

        buffer.seek(0)

        # Prevent size inflation (important!)
        if is_large and buffer.getbuffer().nbytes > original_size_bytes:
            return None  # Skip saving large variant

        return buffer