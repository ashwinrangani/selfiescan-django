from django.urls import path
from . import views

urlpatterns = [
   
    path('',views.upload_selfie, name='upload_selfie'),
    path('generate-barcode/',views.generate_barcode,name='generate_barcode'),
    

]
