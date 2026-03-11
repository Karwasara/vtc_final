from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AreaMaster, SubsidiaryMaster

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ['username', 'email', 'user_type', 'is_staff', 'get_areas']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'address', 'user_type', 'subsidiary', 'areas')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone', 'address', 'user_type', 'subsidiary', 'areas')}),
    )

    # Show many-to-many nicely in list view
    def get_areas(self, obj):
        return ", ".join([a.area_name for a in obj.areas.all()])

    get_areas.short_description = "Areas"

    # Better UI for many-to-many
    filter_horizontal = ('areas',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AreaMaster)
admin.site.register(SubsidiaryMaster)

