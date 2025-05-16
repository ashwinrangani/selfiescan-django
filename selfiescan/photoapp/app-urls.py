from django.urls import path, include
from .views.find_photos import process_selfie
from .views.upload_photos import upload_photos
from .views.auth_views import sign_in, sign_up, sign_out
from .views.profile import profile
from .views.acc_settings import settings, update_username, delete_account
from .views.homepage import homepage
from .views.photographer import create_event, download_qr
from .views.event_detail import event_detail, load_photos, create_branding,remove_branding_logo,start_branding
from .views.event_delete import event_delete,delete_event_photos

from .views.unsubscribe_email import unsubscribe_reminders
from .views.payments.billing_dashboard import billing_dashboard
from .views.payments.payment_webhook import payment_success, payment_webhook
from .views.payments.subscribe import subscribe

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
    path("event/<uuid:event_id>/branding/", create_branding, name="branding"),
    path("event/<uuid:event_id>/branding/remove-logo/", remove_branding_logo, name="remove_branding_logo"),
    path('event/<uuid:event_id>/start-branding/', start_branding, name='start_branding'),
    path('signin/', sign_in, name='signin'),
    path('signout/', sign_out, name='signout'),
    path('signup/', sign_up, name='signup'),
    path('accounts/', include('allauth.urls')),
    path('profile/', profile, name='profile'),
    path('settings/', settings, name='settings'),
    path('settings/update-username/', update_username, name='update_username'),
    path('settings/delete-account/', delete_account, name='delete_account'),
    path('subscribe/', subscribe, name='subscribe'),  # For billing dashboard (no event_id)
    # path('subscribe/<str:event_id>/', subscribe, name='subscribe_with_event'),  # For event-specific uploads
    path('payment/webhook/', payment_webhook, name='payment_webhook'),
    path('payment/success/', payment_success, name='payment_success'),
    path('billing/', billing_dashboard, name='billing_dashboard'),
    path("unsubscribe/<int:user_id>/", unsubscribe_reminders, name="unsubscribe"),

]

