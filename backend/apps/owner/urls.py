from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.owner.views import DashboardAPIView, OccupancyAPIView, ProfitLossAPIView, ReportExportViewSet, TaxReportAPIView

router = DefaultRouter()
router.register("exports", ReportExportViewSet, basename="owner-export")

urlpatterns = [
    path("dashboard/", DashboardAPIView.as_view(), name="owner-dashboard"),
    path("reports/profit-loss/", ProfitLossAPIView.as_view(), name="owner-profit-loss"),
    path("reports/tax/", TaxReportAPIView.as_view(), name="owner-tax"),
    path("reports/occupancy/", OccupancyAPIView.as_view(), name="owner-occupancy"),
]

urlpatterns += router.urls
