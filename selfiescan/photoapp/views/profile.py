from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..forms import updateUserForm, updateProfileForm
from django.http import JsonResponse
from ..models import Profile

@login_required
def profile(request):
    
    profile, created = Profile.objects.get_or_create(user=request.user)
    print(f"Profile created: {created}, User: {request.user.username}")


    if request.method == 'POST':
        form_user = updateUserForm(request.POST, instance=request.user)
        form_profile = updateProfileForm(request.POST, request.FILES, instance=profile)

        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()
            form_profile.save()

            response_data = {
                "success": True,
                "profile_img_url": profile.profile_img.url,
            }
            return JsonResponse(response_data)

        else:
            return JsonResponse({"success": False, "errors": form_user.errors}, status=400)

    else:
        form_user = updateUserForm(instance=request.user)
        form_profile = updateProfileForm(instance=profile)
    
    return render(request, 'profile.html', {'user_form': form_user, 'profile_form': form_profile})
