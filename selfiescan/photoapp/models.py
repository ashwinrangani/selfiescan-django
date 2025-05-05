from re import I
from django.db import models
from django.contrib.auth.models import User
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from sympy import true
from .tasks import process_photo



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_img = models.ImageField(upload_to = 'profile_pics/', default='default.jpg')
    
    def __str__(self):
        return self.user.username


class Event(models.Model):
    photographer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)
    branding_enabled = models.BooleanField(default=False)
    branding_image = models.ImageField(upload_to='branding/', null=True, blank=True)
    branding_text = models.CharField(max_length=100, blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.qr_code:
            qr = qrcode.make(f"http://localhost:8000/find/photos/{self.event_id}/")
            qr_io = BytesIO()
            qr.save(qr_io, format='PNG')
            self.qr_code.save(f"{self.event_id}.png", ContentFile(qr_io.getvalue()), save=False)
        super().save(*args, **kwargs)


def event_photo_path(instance, filename):
    """Generate file path for new photo, organized by photographer and event name."""
    photographer_name = instance.event.photographer.username 
    safe_event_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in instance.event.name)
    return f"photos/{photographer_name}/{safe_event_name}/{filename}"

def event_photo_branded_path(instance, filename):
    photographer_name = instance.event.photographer.username
    safe_event_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in instance.event.name)
    return f"photos/{photographer_name}/{safe_event_name}_branded/{filename}"


class Photo(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=event_photo_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    branded_image = models.ImageField(upload_to=event_photo_branded_path, null=True, blank=True)
    is_branded = models.BooleanField(default=False) 

    def __str__(self):
        return f"Photo {self.id} for Event {self.event.name}"

class FaceEncoding(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="encodings")
    encoding = models.BinaryField(null=True,blank=True)

@receiver(post_save, sender=Photo)
def run_face_encoding_task(sender, instance, created, **kwargs):
    if created:
        process_photo.delay(instance.id)  # Run the Celery task asynchronously


class Subscription(models.Model):
    SUBSCRIPTION_TYPES = (
        ('FREE','Free'),('PER_EVENT','Per Event'),('MONTHLY','Monthly'),('YEARLY','Yearly'),
    )
    photographer = models.ForeignKey(User,on_delete=models.CASCADE)
    subscription_type = models.CharField(max_length=20,choices=SUBSCRIPTION_TYPES,default="FREE")
    photo_count = models.IntegerField(default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    last_notified = models.DateTimeField(null=True, blank=True)
    unsubscribed = models.BooleanField(default=False) #unsubscribe from email reminders
    

    def __str__(self):
        return f"{self.photographer.username} - {self.subscription_type}"

# class EventSubscription(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE)
#     photographer = models.ForeignKey(User,on_delete=models.CASCADE)
#     is_paid = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Event {self.event.name} - Pain: {self.is_paid}"


class Payment(models.Model):
    PAYMENT_TYPES = (
        ('PER_EVENT', 'Per Event'),('YEARLY', 'Yearly'),('MONTHLY','Monthly')
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),('COMPLETED', 'Completed'),('FAILED', 'Failed'),
    )
    photographer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_id = models.CharField(max_length=200, null=True, blank=True)  # Razorpay payment_id
    order_id = models.CharField(max_length=200, null=True, blank=True)  # Razorpay order_id
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - {self.photographer.username} - {self.status}"
