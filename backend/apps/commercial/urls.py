from rest_framework.routers import DefaultRouter

from apps.commercial.views import CommercialDocumentViewSet, CommercialTenantProfileViewSet, CommercialTenantViewSet, CommercialUtilityRecordViewSet

router = DefaultRouter()
router.register("tenants", CommercialTenantViewSet, basename="commercial-tenant")
router.register("profiles", CommercialTenantProfileViewSet, basename="commercial-profile")
router.register("documents", CommercialDocumentViewSet, basename="commercial-document")
router.register("utilities", CommercialUtilityRecordViewSet, basename="commercial-utility")

urlpatterns = router.urls
