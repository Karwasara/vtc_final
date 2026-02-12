from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
#from django.db import models


class SubsidiaryMaster(models.Model):
    subsidiary_code = models.CharField(max_length=10, unique=True)
    subsidiary_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.subsidiary_name} ({self.subsidiary_code})"
    
class AreaMaster(models.Model):
    subsidiary = models.ForeignKey(
    SubsidiaryMaster,
    null=True,
    blank=True,
    on_delete=models.CASCADE,
    related_name="areas"
    )

    area_code = models.CharField(max_length=10)
    area_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('subsidiary', 'area_code')

    def __str__(self):
        return f"{self.area_name} - {self.subsidiary.subsidiary_name}"


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    USER_TYPE_CHOICES = [
        ('vtc', 'VTC'),
        ('aso', 'ASO'),
        ('mm', 'Mine Manager'),
        ('admin', 'Admin'),
    ]

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, null=True, blank=True)

    subsidiary = models.ForeignKey(
        SubsidiaryMaster,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    area = models.ForeignKey(
        AreaMaster,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.username


