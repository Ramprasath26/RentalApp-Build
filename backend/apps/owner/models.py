from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class ReportExport(TimeStampedModel):
    class ReportType(models.TextChoices):
        PROFIT_LOSS = "profit_loss", "Profit and Loss"
        TAX = "tax", "Tax"
        OCCUPANCY = "occupancy", "Occupancy"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATED = "generated", "Generated"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_exports")
    report_type = models.CharField(max_length=30, choices=ReportType.choices)
    date_from = models.DateField()
    date_to = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    file = models.FileField(upload_to="owner/reports/", blank=True)

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} ({self.date_from} - {self.date_to})"
