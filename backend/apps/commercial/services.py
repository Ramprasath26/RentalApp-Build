import re

from apps.common.models import Transaction


def gst_number_is_valid(gst: str) -> bool:
    """GST format: 2-digit state code + 10-char PAN + 1 entity number + Z + 1 check digit."""
    if not gst:
        return False
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return bool(re.match(pattern, gst.upper()))


class CommercialService:
    @staticmethod
    def validate_profile(gst_number: str, license_number: str) -> dict:
        """Validate commercial profile fields. Returns a dict of field errors."""
        errors = {}
        if gst_number and not gst_number_is_valid(gst_number):
            errors["gst_number"] = (
                "GST number must be 15 characters in the standard format "
                "(e.g. 29ABCDE1234F1Z5)."
            )
        if not license_number:
            errors["license_number"] = "Trade license number is required for commercial tenants."
        return errors

    @staticmethod
    def get_maintenance_ledger(unit_id: int):
        """Return maintenance expense transactions for a given commercial unit."""
        return (
            Transaction.objects.filter(
                unit_id=unit_id,
                transaction_type=Transaction.TransactionType.EXPENSE,
                category=Transaction.Category.MAINTENANCE,
            )
            .select_related("property", "unit", "tenant")
            .order_by("-transaction_date")
        )

    @staticmethod
    def get_cam_entries(property_id: int):
        """Return Common Area Maintenance expense transactions for a property."""
        return (
            Transaction.objects.filter(
                property_id=property_id,
                transaction_type=Transaction.TransactionType.EXPENSE,
                category=Transaction.Category.MAINTENANCE,
            )
            .select_related("property", "unit", "tenant")
            .order_by("-transaction_date")
        )
