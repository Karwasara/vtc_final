from django.urls import path

from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'sub'

urlpatterns = [
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('certificate/verify/', views.certificate_verification, name='certificate_verification'),
    path('certificate-verification/', views.certificate_detail, name='certificate_detail'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
