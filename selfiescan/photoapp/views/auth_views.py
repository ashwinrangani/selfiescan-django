from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

def sign_up(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username is already taken')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered')
            else:
                user = User.objects.create_user(username=username, email=email,password=password1)
                user.save()
                messages.success(request, 'Account created successfully')
                return redirect('signin')
        else:
            messages.error(request, 'Password do not match')
    return render(request,'signup.html')   
        


def sign_in(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        print(username, password)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect('upload_selfie')  
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'signin.html')

def sign_out(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('signin')