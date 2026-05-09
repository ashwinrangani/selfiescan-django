import logging
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest
from ..models import Event, Photo, Subscription

logger = logging.getLogger(__name__)


def _collect_s3_fields(photos):
    fields = []
    for photo in photos:
        for field in [
            photo.image,
            photo.thumb_image,
            photo.medium_image,
            photo.large_image,
            photo.branded_image,
        ]:
            if field:
                fields.append(field)
    return fields


def _delete_s3_fields(fields):
    for field in fields:
        try:
            field.delete(save=False)
        except Exception:
            logger.exception("Failed to delete S3 file: %s", field.name)


def _delete_photos_atomic(photos, user):
    """
    Collects S3 fields, deletes DB rows inside a transaction,
    then returns S3 fields for deletion after commit.
    """
    photos = list(photos.select_for_update())
    count = len(photos)

    if not count:
        return []

    s3_fields = _collect_s3_fields(photos)

    Photo.objects.filter(id__in=[p.id for p in photos]).delete()
    Subscription.objects.filter(photographer=user).update(
        photo_count=Greatest(F("photo_count") - count, 0)
    )

    return s3_fields  # caller deletes these after commit


@login_required
def event_delete(request, event_id):
    event = get_object_or_404(Event, event_id=event_id, photographer=request.user)

    if request.method == "POST":
        with transaction.atomic():
            s3_fields = _delete_photos_atomic(
                Photo.objects.filter(event=event), request.user
            )
            event.delete()

        # S3 deletions after DB transaction is committed
        _delete_s3_fields(s3_fields)

        messages.success(request, "Event deleted successfully!")
        return redirect(reverse("photographer"))

    return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))


@login_required
def delete_event_photos(request, event_id):
    event = get_object_or_404(Event, event_id=event_id, photographer=request.user)

    if request.method == "POST":
        with transaction.atomic():
            s3_fields = _delete_photos_atomic(
                Photo.objects.filter(event=event), request.user
            )

        # S3 deletions after DB transaction is committed
        _delete_s3_fields(s3_fields)

        messages.success(request, "All photos deleted successfully!")
        return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))

    return redirect(reverse("event_detail", kwargs={"event_id": event.event_id}))