from rest_framework import permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from apps.common.models import Document, Tenant, Unit, UtilityRecord
from apps.commercial.models import CommercialTenantProfile
from apps.commercial.serializers import (
    CommercialDocumentSerializer,
    CommercialTenantProfileSerializer,
    CommercialTenantSerializer,
    CommercialUtilityRecordSerializer,
)


class CommercialTenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.select_related("unit", "unit__property").filter(unit__module_type=Unit.ModuleType.COMMERCIAL).order_by("display_name")
    serializer_class = CommercialTenantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CommercialTenantProfileViewSet(viewsets.ModelViewSet):
    queryset = CommercialTenantProfile.objects.select_related("tenant", "tenant__unit").all().order_by("legal_name")
    serializer_class = CommercialTenantProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CommercialUtilityRecordViewSet(viewsets.ModelViewSet):
    queryset = UtilityRecord.objects.select_related("property", "unit").filter(unit__module_type=Unit.ModuleType.COMMERCIAL).order_by("-billing_period_end")
    serializer_class = CommercialUtilityRecordSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CommercialDocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("property", "unit", "tenant").filter(module_type=Document.ModuleType.COMMERCIAL).order_by("-created_at")
    serializer_class = CommercialDocumentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
