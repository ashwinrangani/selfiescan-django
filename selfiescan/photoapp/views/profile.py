from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..forms import updateUserForm, updateProfileForm
from django.contrib import messages
from django.http import JsonResponse

@login_required
def profile(request):
    if request.method == 'POST':
        form_user = updateUserForm(request.POST, instance=request.user)
        form_profile = updateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()
            form_profile.save()

            response_data = {
                "success": True,
                "profile_img_url": request.user.profile.profile_img.url,  # ✅ Fixed reference
            }
            messages.success(request, "Profile updated successfully!")
            return JsonResponse(response_data)

        else:
            messages.error(request, "There was an error updating your profile. Please check the fields.")
            return JsonResponse({"success": False, "errors": form_user.errors}, status=400)  # ✅ Fixed return

    else:
        form_user = updateUserForm(instance=request.user)
        form_profile = updateProfileForm(instance=request.user.profile)
    
    return render(request, 'profile.html', {'user_form': form_user, 'profile_form': form_profile})
