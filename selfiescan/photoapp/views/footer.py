from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
import requests
from django.conf import settings

def about_us(request):
    return render(request, 'footer/about_us.html')

def privacy_policy(request):
    return render(request, "footer/privacy_policy.html")

def terms_of_service(request):
    return render(request, "footer/terms_of_service.html")

def cancellation_refund_policy(request):
    return render(request, "footer/cancellation_refund_policy.html")


def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Validate input (basic example)
        if not all([name, email, message]):
            return JsonResponse({'success': False, 'message': 'All fields are required.'})
        
        # turnstile token verification
        turnstile_response = request.POST.get("cf-turnstile-response")

        data = {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": turnstile_response,
        }

        try:
            r = requests.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data=data,
                timeout=5,
            )

            result = r.json()

            if not result.get("success"):
                return JsonResponse({
                    "success": False,
                    "message": "Turnstile verification failed."
                }, status=400)

        except requests.RequestException:
            return JsonResponse({
                "success": False,
                "message": "Verification service unavailable. Please try again."
            }, status=500)

        
        # Send email to support (configure your email backend in settings.py)
        try:
            send_mail(
                subject=f'Contact Us Message from {name}',
                message=f'Name: {name}\nEmail: {email}\nMessage: {message}',
                from_email=email,
                recipient_list=['ashwyn.rangani@gmail.com'],
            )
            return JsonResponse({'success': True, 'message': 'Your message has been sent successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Failed to send message. Please try again later.'})
    
    # Handle GET request to render the Contact Us page
    return render(request, 'footer/contact_us.html')