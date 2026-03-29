from rest_framework.routers import DefaultRouter

from apps.residential.views import ResidentialDocumentViewSet, ResidentialTenantProfileViewSet, ResidentialTenantViewSet, ResidentialUtilityRecordViewSet

router = DefaultRouter()
router.register("tenants", ResidentialTenantViewSet, basename="residential-tenant")
router.register("profiles", ResidentialTenantProfileViewSet, basename="residential-profile")
router.register("documents", ResidentialDocumentViewSet, basename="residential-document")
router.register("utilities", ResidentialUtilityRecordViewSet, basename="residential-utility")

urlpatterns = router.urls
