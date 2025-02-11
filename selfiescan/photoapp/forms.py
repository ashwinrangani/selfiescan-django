from django import forms
from django.contrib.auth.models import User
from .models import Profile  

class updateUserForm(forms.ModelForm):
    class Meta:
        model = User 
        fields = ['first_name', 'last_name', 'email']

class updateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile  
        fields = ['profile_img']
