from django.contrib import admin

from apps.owner.models import ReportExport


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ("owner", "report_type", "date_from", "date_to", "status")
    list_filter = ("report_type", "status")
