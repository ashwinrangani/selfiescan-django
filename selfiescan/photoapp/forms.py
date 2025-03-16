from django import forms
from django.contrib.auth.models import User
from .models import Profile, Event 

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