from django.db import models
from datetime import date, timezone
from django.db import models
from django.forms import ValidationError
from django.conf import settings
# Create your models here.
from django.db import models
from accounts.models import CustomUser
class IndependentWorker(models.Model):
    def validate_age(value):
        today = date.today()
        age = (today - value).days / 365.25
        if age < 18:
            raise ValidationError('Worker must be at least 18 years old.')
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    CATEGORY_CHOICES = [
        ('G', 'General'),
        ('O', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
    ]
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="independent_workers",null=True
    )
    name = models.CharField("Name of Worker",max_length=100, null=True)
    father_or_spouse_name = models.CharField("Father/Spouse Name", max_length=100, null=True)
    ID_Card_number = models.CharField("ID card number of Worker",max_length=100, null=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True)
    caste = models.CharField("Category",max_length=50, choices=CATEGORY_CHOICES, null=True)
    dob = models.DateField("Date of Birth", null=True,validators=[validate_age])
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, null=True)
    aadhar_number = models.CharField(max_length=12, unique=True)
    aadhar_file = models.FileField(upload_to='worker_documents/aadhar/', null=True)

    # ✅ New address fields replacing single 'address'
    village = models.CharField("Village", max_length=100, null=True)
    thana = models.CharField("Thana", max_length=100, null=True)
    po = models.CharField("Post Office", max_length=100, null=True)
    district = models.CharField("District", max_length=100, null=True)
    state = models.CharField("State", max_length=100, null=True)

    mobile = models.CharField("Mobile Number", max_length=10, null=True)
    qualification = models.CharField(max_length=100, null=True)
    photo = models.ImageField(upload_to='worker_documents/photos/', null=True)
    form_o = models.CharField("Form O number", max_length=100, null=True)
    do_form = models.FileField("Form O", upload_to='worker_documents/do_forms/', null=True)

    delete_flag = models.BooleanField(default=False)  # Logical delete
    def __str__(self):
        return self.name

from django.db import models



# Create your models here.


    
from django.db import models

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Rejected', 'Rejected'),
]
TRAINING_TYPE_CHOICES = [
        ('Basic', 'Basic'),
        ('Refresher', 'Refresher'),
        ('Special', 'Special'),
    ]

class TrainingSchedule(models.Model):
    worker = models.ForeignKey(IndependentWorker, on_delete=models.CASCADE, related_name='trainings')
    from_date = models.DateField()
    to_date = models.DateField()
    type_of_training = models.CharField(max_length=20, choices=TRAINING_TYPE_CHOICES, default='Basic')
    nature_of_training = models.CharField(max_length=255, blank=True, null=True)
    contractor_name = models.CharField(max_length=255, blank=True, null=True)
    aso_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    mm_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    vtc_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    # ✅ Approval details
    vtc_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vtc_approvals"
    )
    vtc_approved_at = models.DateTimeField(null=True, blank=True)
    
    aso_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aso_approvals"
    )
    aso_approved_at = models.DateTimeField(null=True, blank=True)

    mm_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mm_approvals"
    )
    mm_approved_at = models.DateTimeField(null=True, blank=True)
    attendance_field_file = models.FileField(upload_to='worker_documents/attendancefield/', null=True)
    certificate_serial_number = models.BigIntegerField(unique=True, null=True, blank=True)
    certificate_serial_number_final = models.CharField(max_length=14, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    certificate_created_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)   # when record first created
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="trainings_created"
    )
    modified_at = models.DateTimeField(auto_now=True)      # updates automatically on save
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="trainings_modified"
    )
    def __str__(self):
        return f"{self.worker.name} Training ({self.from_date} to {self.to_date})"



class TrainingAttendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Holiday', 'Holiday'),
    ]
    training = models.ForeignKey(TrainingSchedule, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    present = models.CharField(max_length=10, choices=STATUS_CHOICES)
    class Meta:
        unique_together = ('training', 'date')  # prevents duplicate entries for same date

class TrainingResult(models.Model):
    training = models.OneToOneField(TrainingSchedule, on_delete=models.CASCADE, related_name='result')
    attendance_field_file = models.FileField(upload_to='worker_documents/attendancefield/', null=True,blank=True)
    performance_appraisal = models.CharField(max_length=20, choices=[
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('Poor', 'Poor')
    ])
    remarks = models.TextField(blank=True, null=True)
   
    
    
    
