from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from apps.common.models import Property, RentLedger, Tenant, Transaction, Unit


class OwnerDashboardService:
    @staticmethod
    def summary():
        income_total = Transaction.objects.filter(transaction_type=Transaction.TransactionType.INCOME).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]
        expense_total = Transaction.objects.filter(transaction_type=Transaction.TransactionType.EXPENSE).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]

        pending_qs = RentLedger.objects.filter(status__in=[RentLedger.Status.PENDING, RentLedger.Status.PARTIAL, RentLedger.Status.OVERDUE])
        pending_rent_count = pending_qs.count()
        pending_rent_amount = pending_qs.aggregate(
            total=Coalesce(Sum("due_amount") - Sum("paid_amount"), Decimal("0.00"))
        )["total"]

        return {
            "properties": Property.objects.count(),
            "occupied_units": Unit.objects.filter(status=Unit.Status.OCCUPIED).count(),
            "active_tenants": Tenant.objects.filter(status=Tenant.Status.ACTIVE).count(),
            "income_total": income_total,
            "expense_total": expense_total,
            "net_total": income_total - expense_total,
            "pending_rent_count": pending_rent_count,
            "pending_rent_amount": pending_rent_amount,
        }

    @staticmethod
    def profit_loss(date_from=None, date_to=None, user=None):
        queryset = Transaction.objects.all()
        if user is not None:
            queryset = queryset.filter(property__owner=user)
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)

        return queryset.values("category").annotate(
            income=Coalesce(Sum("amount", filter=Q(transaction_type=Transaction.TransactionType.INCOME)), Decimal("0.00")),
            expense=Coalesce(Sum("amount", filter=Q(transaction_type=Transaction.TransactionType.EXPENSE)), Decimal("0.00")),
            entries=Count("id"),
        ).order_by("category")

    @staticmethod
    def occupancy_summary(user=None):
        """Return unit counts by status; optionally scoped to a specific owner."""
        qs = Unit.objects.all()
        if user is not None:
            qs = qs.filter(property__owner=user)
        status_counts = qs.values("status").annotate(count=Count("id"))
        result = {row["status"]: row["count"] for row in status_counts}
        total = sum(result.values())
        occupied = result.get(Unit.Status.OCCUPIED, 0)
        return {
            "total_units": total,
            "vacant": result.get(Unit.Status.VACANT, 0),
            "occupied": occupied,
            "maintenance": result.get(Unit.Status.MAINTENANCE, 0),
            "occupancy_rate": round(occupied / total * 100, 1) if total else 0.0,
        }
