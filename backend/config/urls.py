from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.health import healthz

urlpatterns = [
    path("healthz", healthz, name="healthz"),   # k8s liveness / readiness probe
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/commercial/", include("apps.commercial.urls")),
    path("api/v1/residential/", include("apps.residential.urls")),
    path("api/v1/owner/", include("apps.owner.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
