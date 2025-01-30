from django.urls import path
from .views.views import upload_selfie, generate_barcode
from .views.auth_views import sign_in, sign_up, sign_out

urlpatterns = [
    path('', upload_selfie, name='upload_selfie'),
    path('generate-barcode/', generate_barcode, name='generate_barcode'),
    path('signin/', sign_in, name='signin'),
    path('signout/', sign_out, name='signout'),
    path('signup/', sign_up, name='signup'),
]

