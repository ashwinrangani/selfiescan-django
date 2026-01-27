from PIL import Image, ImageOps
from io import BytesIO

VARIANTS = { "thumb": {"size": (600, 600),"quality": 70},
"medium": {"size": (1600, 1600), "quality": 80},
"large": {"size": (3000, 3000), "quality": 90}, }

def generate_variant(image_field, size, quality):
    with image_field.open("rb") as f:
        img = Image.open(f)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img = ImageOps.contain(img, size)

        buffer = BytesIO()
        img.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True
        )
        buffer.seek(0)
        return buffer
