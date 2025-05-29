from django.shortcuts import render

def about_us(request):
    
    return render(request,'footer/about_us.html')


def privacy_policy(request):
    return render(request,"footer/privacy_policy.html")

def terms_of_service(request):
    return render(request,"footer/terms_of_service.html")

def cancellation_refund_policy(request):
    return render(request, "footer/cancellation_refund_policy.html")