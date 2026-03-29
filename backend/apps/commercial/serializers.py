from rest_framework import serializers

from apps.common.models import Document, Tenant, Unit, UtilityRecord
from apps.common.serializers import DocumentSerializer, TenantSerializer, UtilityRecordSerializer
from apps.commercial.models import CommercialTenantProfile


class CommercialTenantSerializer(TenantSerializer):
    def validate(self, attrs):
        attrs["tenant_type"] = Tenant.TenantType.BUSINESS
        unit = attrs.get("unit") or getattr(self.instance, "unit", None)
        if unit and unit.module_type != Unit.ModuleType.COMMERCIAL:
            raise serializers.ValidationError("Commercial tenants must be assigned to a commercial unit.")
        return attrs


class CommercialTenantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommercialTenantProfile
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class CommercialUtilityRecordSerializer(UtilityRecordSerializer):
    def validate_unit(self, unit):
        if unit.module_type != Unit.ModuleType.COMMERCIAL:
            raise serializers.ValidationError("Only commercial units are allowed.")
        return unit


class CommercialDocumentSerializer(DocumentSerializer):
    def validate(self, attrs):
        attrs["module_type"] = Document.ModuleType.COMMERCIAL
        return super().validate(attrs)
