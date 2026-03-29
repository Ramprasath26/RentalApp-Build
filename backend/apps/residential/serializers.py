from rest_framework import serializers

from apps.common.models import Document, Tenant, Unit, UtilityRecord
from apps.common.serializers import DocumentSerializer, TenantSerializer, UtilityRecordSerializer
from apps.residential.models import ResidentialTenantProfile


class ResidentialTenantSerializer(TenantSerializer):
    def validate(self, attrs):
        attrs["tenant_type"] = Tenant.TenantType.INDIVIDUAL
        unit = attrs.get("unit") or getattr(self.instance, "unit", None)
        if unit and unit.module_type != Unit.ModuleType.RESIDENTIAL:
            raise serializers.ValidationError("Residential tenants must be assigned to a residential unit.")
        return attrs


class ResidentialTenantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialTenantProfile
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class ResidentialUtilityRecordSerializer(UtilityRecordSerializer):
    def validate_unit(self, unit):
        if unit.module_type != Unit.ModuleType.RESIDENTIAL:
            raise serializers.ValidationError("Only residential units are allowed.")
        return unit


class ResidentialDocumentSerializer(DocumentSerializer):
    def validate(self, attrs):
        attrs["module_type"] = Document.ModuleType.RESIDENTIAL
        return super().validate(attrs)
