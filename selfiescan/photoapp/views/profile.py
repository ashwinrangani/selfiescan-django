from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..forms import updateUserForm, updateProfileForm

@login_required
def profile(request):
    if request.method == 'POST':
        form_user = updateUserForm(request.POST, instance=request.user)
        form_profile = updateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()
            form_profile.save()
            return redirect('profile')
    else:
        form_user = updateUserForm(request.POST, instance=request.user)
        form_profile = updateProfileForm(request.POST, request.FILES, instance=request.user.profile)
    
    return render(request, 'profile.html', {'form_user':form_user,'form_profile': form_profile})