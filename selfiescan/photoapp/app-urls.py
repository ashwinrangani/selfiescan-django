from django.urls import path, include
from .views.find_photos import process_selfie
from .views.upload_photos import upload_photos
from .views.auth_views import sign_in, sign_up, sign_out
from .views.profile import profile
from .views.acc_settings import settings, update_username, delete_account
from .views.homepage import homepage
from .views.photographer import create_event, download_qr
from .views.event_detail import event_detail, load_photos
from .views.event_delete import event_delete,delete_event_photos

urlpatterns = [
    path("", homepage, name='homepage'),
    path("upload/photos/<uuid:event_id>/", upload_photos, name="upload_photos"),
    path("find/photos/<uuid:event_id>/", process_selfie, name='find_photos'),
    path("photographer/", create_event,name="photographer"),
    path("event/<uuid:event_id>/",event_detail, name="event_detail"),
    path("event/<uuid:event_id>/photos/", load_photos, name="load_photos"),
    path("event/<uuid:event_id>/delete_event", event_delete, name="event_delete"),
    path('event/<uuid:event_id>/delete_photos/', delete_event_photos, name='delete_event_photos'),
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

