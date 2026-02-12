from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import CustomUser, AreaMaster, SubsidiaryMaster

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'is_staff',"area"]
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'address', 'user_type',"area")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone', 'address', 'user_type',"area")}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AreaMaster)
admin.site.register(SubsidiaryMaster)
