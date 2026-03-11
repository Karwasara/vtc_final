from django.urls import path
from mm import views as mm_views
from . import views
from django.conf import settings
from django.conf.urls.static import static
app_name = 'vtc'

urlpatterns = [
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('workers/', views.worker_list, name='worker_list'),
    path('workers/add/', views.add_worker, name='add_worker'),
    path('workers/<int:pk>/edit/', views.edit_worker, name='edit_worker'),
    path('workers/<int:pk>/delete/', views.delete_worker, name='delete_worker'),
    path('schedule_training/<int:pk>/', views.schedule_training, name='schedule_training'),
    path('schedule_training/<int:pk>/edit/', views.edit_training, name='edit_training'),
    path('schedule_training/<int:pk>/delete/', views.delete_training, name='delete_training'),
    path('attendance_result/<int:pk>/', views.add_training_attendance_and_result, name='add_training_attendance_and_result'),
    path('scheduled-trainings/', views.scheduled_training_list, name='scheduled_training_list'),
    path('to_schedule_training/', views.to_schedule_training, name='to_schedule_training'),
    path('worker/<int:pk>/view/', views.view_worker, name='view_worker'),
   
    path('certificate-verification/', views.certificate_detail, name='certificate_detail'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)