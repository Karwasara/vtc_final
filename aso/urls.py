from django.urls import path
from . import views
app_name = 'aso'

urlpatterns = [
    # path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('received_trainings/', views.vtc_forwarded_training_list, name='received_training_list'),
    path('forwarded_trainings/', views.aso_forwarded_training_list, name='forwarded_training_list'),
    path('forward_to_mm/<int:pk>/', views.forward_to_mm, name='forward_to_mm'),
    path('reject_training/<int:pk>/', views.reject_training, name='reject_training'),
    path('training_detail/<int:pk>/', views.training_detail, name='training_detail'),
    path('approved-worker/<int:pk>/', views.approved_worker_detail, name='approved_worker_detail'),
    path('certificate-verification/', views.certificate_detail, name='certificate_detail'),
   
    
]