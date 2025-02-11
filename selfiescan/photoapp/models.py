from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=255)
    barcode_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

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