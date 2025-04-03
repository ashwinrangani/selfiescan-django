from django.db import models
from django.contrib.auth.models import User
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import process_photo



# Create your models here.
class Event(models.Model):
    photographer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)

    def save(self, *args, **kwargs):
        if not self.qr_code:
            qr = qrcode.make(f"http://localhost:8000/find/photos/{self.event_id}/")
            qr_io = BytesIO()
            qr.save(qr_io, format='PNG')
            self.qr_code.save(f"{self.event_id}.png", ContentFile(qr_io.getvalue()), save=False)
        super().save(*args, **kwargs)


def event_photo_path(instance, filename):
    """Generate file path for new photo, organized by photographer and event name."""
    photographer_name = instance.event.photographer.username  # or use ID if needed
    safe_event_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in instance.event.name)
    return f"photos/{photographer_name}/{safe_event_name}/{filename}"


class Photo(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=event_photo_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class FaceEncoding(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="encodings")
    encoding = models.BinaryField(null=True,blank=True)

@receiver(post_save, sender=Photo)
def run_face_encoding_task(sender, instance, created, **kwargs):
    if created:
        process_photo.delay(instance.id)  # Run the Celery task asynchronously


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_img = models.ImageField(upload_to = 'profile_pics/', default='default.jpg')
    
    def __str__(self):
        return self.user.username