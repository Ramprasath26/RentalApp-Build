from rest_framework import permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from apps.common.models import Document, Tenant, Unit, UtilityRecord
from apps.residential.models import ResidentialTenantProfile
from apps.residential.serializers import (
    ResidentialDocumentSerializer,
    ResidentialTenantProfileSerializer,
    ResidentialTenantSerializer,
    ResidentialUtilityRecordSerializer,
)


class ResidentialTenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.select_related("unit", "unit__property").filter(unit__module_type=Unit.ModuleType.RESIDENTIAL).order_by("display_name")
    serializer_class = ResidentialTenantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ResidentialTenantProfileViewSet(viewsets.ModelViewSet):
    queryset = ResidentialTenantProfile.objects.select_related("tenant", "tenant__unit").all().order_by("tenant__display_name")
    serializer_class = ResidentialTenantProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ResidentialUtilityRecordViewSet(viewsets.ModelViewSet):
    queryset = UtilityRecord.objects.select_related("property", "unit").filter(unit__module_type=Unit.ModuleType.RESIDENTIAL).order_by("-billing_period_end")
    serializer_class = ResidentialUtilityRecordSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ResidentialDocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("property", "unit", "tenant").filter(module_type=Document.ModuleType.RESIDENTIAL).order_by("-created_at")
    serializer_class = ResidentialDocumentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
