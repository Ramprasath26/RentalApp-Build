from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import Tenant, TimeStampedModel


class CommercialTenantProfile(TimeStampedModel):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="commercial_profile")
    legal_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    registered_address = models.TextField(blank=True)
    maintenance_notes = models.TextField(blank=True)

    def clean(self) -> None:
        if self.tenant.tenant_type != Tenant.TenantType.BUSINESS:
            raise ValidationError("Commercial profiles require a business tenant.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.legal_name or self.tenant.display_name
