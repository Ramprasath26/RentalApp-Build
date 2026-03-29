from decimal import Decimal

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.owner.models import ReportExport
from apps.owner.serializers import DashboardSummarySerializer, OccupancySummarySerializer, ReportExportSerializer
from apps.owner.services import OwnerDashboardService


class DashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        serializer = DashboardSummarySerializer(OwnerDashboardService.summary())
        return Response(serializer.data)


class ProfitLossAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        user = request.user if request.user.is_authenticated else None
        return Response(list(OwnerDashboardService.profit_loss(date_from=date_from, date_to=date_to, user=user)))


class TaxReportAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        user = request.user if request.user.is_authenticated else None

        breakdown = list(OwnerDashboardService.profit_loss(date_from=date_from, date_to=date_to, user=user))
        income_total = sum((row["income"] for row in breakdown), Decimal("0.00"))
        expense_total = sum((row["expense"] for row in breakdown), Decimal("0.00"))

        return Response(
            {
                "assessment_window": {
                    "date_from": date_from,
                    "date_to": date_to,
                },
                "income_total": income_total,
                "expense_total": expense_total,
                "net_total": income_total - expense_total,
                "breakdown": breakdown,
            }
        )


class OccupancyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        serializer = OccupancySummarySerializer(OwnerDashboardService.occupancy_summary(user=user))
        return Response(serializer.data)


class ReportExportViewSet(viewsets.ModelViewSet):
    queryset = ReportExport.objects.select_related("owner").all().order_by("-created_at")
    serializer_class = ReportExportSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        owner = serializer.validated_data.get("owner")
        if not owner and self.request.user.is_authenticated:
            serializer.save(owner=self.request.user)
            return
        serializer.save()
