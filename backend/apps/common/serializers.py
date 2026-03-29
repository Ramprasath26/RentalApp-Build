from decimal import Decimal

from rest_framework import serializers

from apps.common.models import ActivityLog, DepositLedger, Document, Property, Receipt, RentLedger, Tenant, Transaction, Unit, User, UtilityRecord


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role")
        read_only_fields = ("id",)


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "owner")


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class UtilityRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityRecord
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "consumption_units")


_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv",
}
_MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "original_file_name")

    def validate_file(self, uploaded_file):
        if uploaded_file.size > _MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("File size must not exceed 15 MB.")
        ct = getattr(uploaded_file, "content_type", "") or ""
        if ct not in _ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                f"File type '{ct}' is not allowed. "
                "Permitted: PDF, images, Word, Excel, text/CSV."
            )
        return uploaded_file

    def create(self, validated_data):
        uploaded_file = validated_data.get("file")
        if uploaded_file and not validated_data.get("original_file_name"):
            validated_data["original_file_name"] = uploaded_file.name
            validated_data["content_type"] = getattr(uploaded_file, "content_type", "")
        return super().create(validated_data)


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class RentLedgerSerializer(serializers.ModelSerializer):
    pending_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tenant_name = serializers.CharField(source="tenant.display_name", read_only=True)

    class Meta:
        model = RentLedger
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "paid_amount", "status")


class RentPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    payment_mode = serializers.CharField(max_length=30, required=False, default="")
    notes = serializers.CharField(required=False, default="")
    transaction_date = serializers.DateField(required=False)


class DepositLedgerSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.display_name", read_only=True)

    class Meta:
        model = DepositLedger
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", default="system")

    class Meta:
        model = ActivityLog
        fields = ["id", "username", "action", "resource_type", "resource_id", "details", "ip_address", "created_at"]


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "is_active", "is_staff", "date_joined", "last_login"]

