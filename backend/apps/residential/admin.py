from django.contrib import admin

from apps.residential.models import ResidentialTenantProfile


@admin.register(ResidentialTenantProfile)
class ResidentialTenantProfileAdmin(admin.ModelAdmin):
    list_display = ("tenant", "occupation", "family_size", "emergency_contact")
    search_fields = ("tenant__display_name", "pan_number", "aadhar_number")
