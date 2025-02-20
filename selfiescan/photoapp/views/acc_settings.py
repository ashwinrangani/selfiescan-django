from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def settings(request):
    return render(request, 'settings.html', {'user':request.user})


@login_required
def update_username(request):
    if request.method == "POST":
        data = json.loads(request.body)
        new_username = data.get("username").strip()

        if not new_username:  # Ensure username is not empty
            return JsonResponse({"success": False, "message": "Username cannot be empty."}, status=400)

        # Check if username exists (excluding the current user)
        if User.objects.filter(username=new_username).exists():
            return JsonResponse({"success": False, "message": "Username already taken."}, status=400)

        # Save new username
        request.user.username = new_username
        request.user.save()
        return JsonResponse({"success": True, "message": "Username updated successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)


@login_required
def delete_account(request):
    if request.method == "POST":
        request.user.delete()
        return JsonResponse({"success" : True})
    return JsonResponse({"success": False}, status=400)
