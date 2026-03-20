from django.urls import path
from . import views
app_name = 'mm'
urlpatterns = [
    # path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('forwarded_trainings/', views.aso_forwarded_training_list, name='forwarded_training_list'),
    #path('forwarded_workers/', views.hod_forwarded_workers_list, name='forwarded_workers'),
    #path('mm_forwarded_workers/', views.mm_forwarded_workers_list, name='mm_forwarded_workers'),
    path('approved-worker/<int:pk>/', views.approved_worker_detail, name='approved_worker_detail'),
    path('training/<int:training_id>/form_a_pdf/', views.generate_form_a_pdf, name='generate_form_a_pdf'),
    #path('worker/<int:pk>/detail/', views.forward_to_vtc, name='forward_to_vtc')
    path('certificate/verify/', views.certificate_verification, name='certificate_verification'),
    path('certificate-verification/', views.certificate_detail, name='certificate_detail'),
    
]