from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.common.models import ActivityLog, DepositLedger, Document, Property, Receipt, RentLedger, Tenant, Transaction, Unit, User, UtilityRecord


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Rental Roles", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "property_type", "city", "state", "owner")
    search_fields = ("name", "city", "state")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("unit_code", "property", "module_type", "status")
    list_filter = ("module_type", "status")


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("display_name", "tenant_type", "unit", "rent_amount", "status")
    list_filter = ("tenant_type", "status")
    search_fields = ("display_name", "email", "phone")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_type", "category", "amount", "property", "transaction_date")
    list_filter = ("transaction_type", "category", "currency")


@admin.register(UtilityRecord)
class UtilityRecordAdmin(admin.ModelAdmin):
    list_display = ("unit", "utility_type", "billing_period_start", "billing_period_end", "bill_amount")
    list_filter = ("utility_type", "billing_model")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_file_name", "module_type", "document_type", "property", "uploaded_by")
    list_filter = ("module_type", "document_type")


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "transaction", "receipt_date", "generation_status")
    list_filter = ("generation_status",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "resource_type", "resource_id", "ip_address", "created_at")
    list_filter = ("action",)
    readonly_fields = ("user", "action", "resource_type", "resource_id", "details", "ip_address", "created_at")


@admin.register(RentLedger)
class RentLedgerAdmin(admin.ModelAdmin):
    list_display = ("tenant", "period_month", "period_year", "due_amount", "paid_amount", "status")
    list_filter = ("status",)


@admin.register(DepositLedger)
class DepositLedgerAdmin(admin.ModelAdmin):
    list_display = ("tenant", "entry_type", "amount", "date")
    list_filter = ("entry_type",)
