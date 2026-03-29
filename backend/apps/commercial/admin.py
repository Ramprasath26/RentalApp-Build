from django.contrib import admin

from apps.commercial.models import CommercialTenantProfile


@admin.register(CommercialTenantProfile)
class CommercialTenantProfileAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "tenant", "gst_number", "license_number")
    search_fields = ("legal_name", "gst_number", "license_number")
