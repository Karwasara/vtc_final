from django.urls import path

from . import views

app_name = 'sub'

urlpatterns = [
    
    path('dashboard/', views.dashboard, name='dashboard'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
