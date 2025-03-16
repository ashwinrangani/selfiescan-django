from django.urls import path, include
from .views.upload_selfie import process_selfie, upload_photos
from .views.auth_views import sign_in, sign_up, sign_out
from .views.profile import profile
from .views.acc_settings import settings, update_username, delete_account
from .views.homepage import homepage
from .views.photographer import create_event, download_qr

urlpatterns = [
    path("", homepage, name='homepage'),
    path("upload/photos", upload_photos, name='upload_photos'),
    path("upload/selfie", process_selfie, name='process_selfie'),
    path("photographer/", create_event,name="photographer"),
    path("event/<uuid:event_id>/download_qr/", download_qr,name="download_qr"),
    path('signin/', sign_in, name='signin'),
    path('signout/', sign_out, name='signout'),
    path('signup/', sign_up, name='signup'),
    path('accounts/', include('allauth.urls')),
    path('profile/', profile, name='profile'),
    path('settings/', settings, name='settings'),
    path('settings/update-username/', update_username, name='update_username'),
    path('settings/delete-account/', delete_account, name='delete_account'),
]

