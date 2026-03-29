from rest_framework import serializers

from apps.owner.models import ReportExport


class DashboardSummarySerializer(serializers.Serializer):
    properties = serializers.IntegerField()
    occupied_units = serializers.IntegerField()
    active_tenants = serializers.IntegerField()
    income_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    expense_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_rent_count = serializers.IntegerField()
    pending_rent_amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class OccupancySummarySerializer(serializers.Serializer):
    total_units = serializers.IntegerField()
    vacant = serializers.IntegerField()
    occupied = serializers.IntegerField()
    maintenance = serializers.IntegerField()
    occupancy_rate = serializers.FloatField()


class ReportExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportExport
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
