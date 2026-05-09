from django import forms
from django.contrib.auth.models import User
from .models import Profile, Event 
from allauth.account.forms import SignupForm
import requests
from django.conf import settings

class updateUserForm(forms.ModelForm):
    class Meta:
        model = User 
        fields = ['first_name', 'last_name', 'email']

class updateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile  
        fields = ['profile_img']

class EventRegistration(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["name", "date", "location"]

class CustomSignupForm(SignupForm):

    def clean(self):
        cleaned_data = super().clean()

        token = self.data.get("cf-turnstile-response")

        if not token:
            raise forms.ValidationError(
                "Please complete the Turnstile verification."
            )

        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": settings.TURNSTILE_SECRET_KEY,
                "response": token,
            },
            timeout=10,
        )

        result = response.json()

        if not result.get("success"):
            raise forms.ValidationError(
                "Turnstile verification failed."
            )

        return cleaned_data