from django.urls import path, include
from .views.views import upload_selfie, generate_barcode
from .views.auth_views import sign_in, sign_up, sign_out
from .views.profile import profile
from .views.acc_settings import settings, update_username, delete_account

urlpatterns = [
    path("", upload_selfie, name='upload_selfie'),
    path('generate-barcode/', generate_barcode, name='generate_barcode'),
    path('signin/', sign_in, name='signin'),
    path('signout/', sign_out, name='signout'),
    path('signup/', sign_up, name='signup'),
    path('accounts/', include('allauth.urls')),
    path('profile/', profile, name='profile'),
    path('settings/', settings, name='settings'),
    path('settings/update-username/', update_username, name='update_username'),
    path('settings/delete-account/', delete_account, name='delete_account'),
]

