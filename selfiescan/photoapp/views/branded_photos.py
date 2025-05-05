import cv2
import numpy as np
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ..models import Photo
import os

def overlay_logo(base_img, logo_path, position='bottom-right', scale=0.2, opacity=0.6):
    logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
    if logo is None or logo.shape[2] != 4:
        return base_img  # Fallback to original if logo is invalid

    # Resize
    logo_h, logo_w = logo.shape[:2]
    base_h, base_w = base_img.shape[:2]
    new_w = int(base_w * scale)
    new_h = int(logo_h * (new_w / logo_w))
    logo = cv2.resize(logo, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Split channels
    b, g, r, a = cv2.split(logo)
    alpha_logo = a.astype(float) / 255 * opacity
    logo_rgb = cv2.merge((b, g, r))

    # Position
    if position == 'bottom-right':
        x, y = base_w - new_w - 10, base_h - new_h - 10
    else:
        x, y = 10, 10  # default

    roi = base_img[y:y+new_h, x:x+new_w].astype(float)

    for c in range(3):
        roi[..., c] = (1 - alpha_logo) * roi[..., c] + alpha_logo * logo_rgb[..., c]

    base_img[y:y+new_h, x:x+new_w] = roi.astype(np.uint8)
    return base_img

def serve_branded_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    event = photo.event
    image_path = photo.image.path
    img = cv2.imread(image_path)
    if img is None:
        return HttpResponse("Image not found", status=404)

    if event.branding_enabled:
        if event.branding_image:
            # Apply logo branding
            logo_path = event.branding_image.path
            if os.path.exists(logo_path):
                img = overlay_logo(img, logo_path, position='bottom-right', scale=0.15, opacity=0.6)
        elif event.branding_text:
            # Apply text branding
            text = event.branding_text
            font = cv2.FONT_HERSHEY_TRIPLEX
            font_scale = round(min(img.shape[1], img.shape[0]) / 1000, 2) + 0.5
            font_color = (235, 235, 235)  # Light gray
            thickness = 2
            margin = 30

            # Get text size
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            height, width = img.shape[:2]

            # Position: bottom right
            x = width - text_width - margin
            y = height - margin

            # Draw semi-black rounded rectangle
            overlay = img.copy()
            rect_x1, rect_y1 = x - 20, y - text_height - 20
            rect_x2, rect_y2 = x + text_width + 20, y + 10
            cv2.rectangle(overlay, (rect_x1, rect_y1), (rect_x2, rect_y2), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

            # Add the text
            cv2.putText(img, text, (x, y), font, font_scale, font_color, thickness, cv2.LINE_AA)

    _, img_encoded = cv2.imencode('.webp', img, [cv2.IMWRITE_WEBP_QUALITY, 80])
    return HttpResponse(img_encoded.tobytes(), content_type='image/webp')