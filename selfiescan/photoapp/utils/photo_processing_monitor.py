from django.db.models import Count, Q
from ..models import Event, Photo

def get_unprocessed_photo_groups():
    """
    Returns list of event info where some photos are unprocessed.
    """
    qs = (
        Photo.objects
        .values('event')
        .annotate(
            total_photos=Count('id'),
            unprocessed_count=Count('id', filter=Q(is_processed=False))
        )
        .filter(unprocessed_count__gt=0)
    )

    result = []
    for item in qs:
        event = Event.objects.get(id=item["event"])
        result.append({
            "event": event,
            "photographer": event.photographer,
            "unprocessed_count": item["unprocessed_count"],
            "total_photos": item["total_photos"],
        })
    return result

