from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import Tenant, TimeStampedModel


class ResidentialTenantProfile(TimeStampedModel):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="residential_profile")
    aadhar_number = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    family_size = models.PositiveIntegerField(default=1)
    emergency_contact = models.CharField(max_length=120, blank=True)

    def clean(self) -> None:
        if self.tenant.tenant_type != Tenant.TenantType.INDIVIDUAL:
            raise ValidationError("Residential profiles require an individual tenant.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.tenant.display_name
