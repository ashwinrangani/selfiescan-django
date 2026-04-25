import boto3
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from ..models import Event
import uuid
import os


@login_required
def get_presigned_url(request, event_id):
    event = get_object_or_404(Event, event_id=event_id)

    file_name = request.GET.get("file_name")
    file_type = request.GET.get("file_type")

    if not file_name or not file_type:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    # ✅ Match your model path logic
    name, ext = os.path.splitext(file_name)
    unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

    file_key = f"photos/photographer_{event.photographer.id}/event_{event.event_id}/originals/{unique_name}"

    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": file_key,
                "ContentType": file_type,
                "CacheControl": "public, max-age=31536000, immutable",
            },
            ExpiresIn=3600,
        )

        return JsonResponse({
            "url": url,
            "file_key": file_key
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)