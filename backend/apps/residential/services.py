import re
from datetime import date

from apps.common.models import Tenant


def aadhar_is_valid(aadhar: str) -> bool:
    """Aadhar numbers are exactly 12 digits."""
    return bool(re.match(r"^\d{12}$", aadhar)) if aadhar else False


def pan_is_valid(pan: str) -> bool:
    """PAN format: 5 letters + 4 digits + 1 letter (e.g. ABCDE1234F)."""
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan.upper())) if pan else False


class ResidentialService:
    @staticmethod
    def validate_profile(aadhar_number: str, pan_number: str) -> dict:
        """Validate residential profile identity fields. Returns a dict of field errors."""
        errors = {}
        if aadhar_number and not aadhar_is_valid(aadhar_number):
            errors["aadhar_number"] = "Aadhar number must be exactly 12 digits."
        if pan_number and not pan_is_valid(pan_number):
            errors["pan_number"] = "PAN must follow the format AAAAA9999A (e.g. ABCDE1234F)."
        return errors

    @staticmethod
    def get_overdue_tenants(as_of: date | None = None):
        """Return active individual tenants whose lease end date has passed."""
        ref = as_of or date.today()
        return (
            Tenant.objects.filter(
                status=Tenant.Status.ACTIVE,
                tenant_type=Tenant.TenantType.INDIVIDUAL,
                end_date__lt=ref,
            )
            .select_related("unit", "unit__property")
            .order_by("end_date")
        )

    @staticmethod
    def get_rent_due_schedule(unit_id: int):
        """Return active tenants for a unit with their billing schedule details."""
        return (
            Tenant.objects.filter(
                unit_id=unit_id,
                status=Tenant.Status.ACTIVE,
            )
            .select_related("unit", "unit__property")
            .values(
                "id",
                "display_name",
                "rent_amount",
                "billing_cycle",
                "start_date",
                "end_date",
                "deposit_amount",
            )
        )
