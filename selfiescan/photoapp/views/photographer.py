from django.shortcuts import render


def photographer(request):
    return render(request, "photographer.html")