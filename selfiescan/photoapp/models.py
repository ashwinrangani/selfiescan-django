from django.db import models
from django.contrib.auth.models import User
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

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
            qr = qrcode.make(f"https://localhost:8000/event/{self.event_id}/")
            qr_io = BytesIO()
            qr.save(qr_io, format='PNG')
            self.qr_code.save(f"{self.event_id}.png", ContentFile(qr_io.getvalue()), save=False)
        super().save(*args, **kwargs)


class Photo(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="photos/")
    face_embedding = models.JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_img = models.ImageField(upload_to = 'profile_pics/', default='default.jpg')
    
    def __str__(self):
        return self.user.username