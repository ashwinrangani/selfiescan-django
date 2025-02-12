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
        form_user = updateUserForm(instance=request.user)
        form_profile = updateProfileForm(instance=request.user.profile)

    print('User First Name:', form_user.instance.first_name)  # Corrected print statement

    return render(request, 'profile.html', {'user_form': form_user, 'profile_form': form_profile})
