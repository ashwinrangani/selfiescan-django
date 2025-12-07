from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile
from allauth.account.signals import user_signed_up
from photoapp.tasks import send_welcome_email_task

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:  
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


@receiver(user_signed_up)
def welcome_email_after_signup(request, user, **kwargs):
    send_welcome_email_task.delay(user.id, user.email)
