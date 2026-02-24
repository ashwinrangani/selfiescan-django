import boto3
from botocore.client import Config
from django.conf import settings
from urllib.parse import quote


def generate_presigned_download(image_field, expires=3600):
    if not image_field:
        return None

    s3 = boto3.client(
        "s3",
        region_name="ap-south-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        
    )

    key = image_field.name
    filename = key.split("/")[-1]

    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": key,
            "ResponseContentDisposition":
                f'attachment; filename="{quote(filename)}"',
        },
        ExpiresIn=expires,
    )

