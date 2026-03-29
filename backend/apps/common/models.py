from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)

    def __str__(self) -> str:
        return self.get_full_name() or self.username


class Property(TimeStampedModel):
    class PropertyType(models.TextChoices):
        COMMERCIAL = "commercial", "Commercial"
        RESIDENTIAL = "residential", "Residential"
        MIXED = "mixed", "Mixed"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_properties")
    name = models.CharField(max_length=255)
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=120, default="India")

    def __str__(self) -> str:
        return self.name


class Unit(TimeStampedModel):
    class ModuleType(models.TextChoices):
        COMMERCIAL = "commercial", "Commercial"
        RESIDENTIAL = "residential", "Residential"

    class Status(models.TextChoices):
        VACANT = "vacant", "Vacant"
        OCCUPIED = "occupied", "Occupied"
        MAINTENANCE = "maintenance", "Maintenance"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="units")
    unit_code = models.CharField(max_length=50)
    module_type = models.CharField(max_length=20, choices=ModuleType.choices)
    floor = models.CharField(max_length=50, blank=True)
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.VACANT)

    class Meta:
        unique_together = ("property", "unit_code")

    def __str__(self) -> str:
        return f"{self.property.name} - {self.unit_code}"


class Tenant(TimeStampedModel):
    class TenantType(models.TextChoices):
        BUSINESS = "business", "Business"
        INDIVIDUAL = "individual", "Individual"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        EXITED = "exited", "Exited"

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="tenants")
    tenant_type = models.CharField(max_length=20, choices=TenantType.choices)
    display_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2)
    billing_cycle = models.CharField(max_length=30, default="monthly")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    def clean(self) -> None:
        if self.tenant_type == self.TenantType.BUSINESS and self.unit.module_type != Unit.ModuleType.COMMERCIAL:
            raise ValidationError("Business tenants must belong to a commercial unit.")
        if self.tenant_type == self.TenantType.INDIVIDUAL and self.unit.module_type != Unit.ModuleType.RESIDENTIAL:
            raise ValidationError("Individual tenants must belong to a residential unit.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.display_name


class Transaction(TimeStampedModel):
    class TransactionType(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    class PaidBy(models.TextChoices):
        OWNER = "owner", "Owner"
        TENANT = "tenant", "Tenant"

    class Category(models.TextChoices):
        RENT = "rent", "Rent"
        DEPOSIT = "deposit", "Deposit"
        MAINTENANCE = "maintenance", "Maintenance"
        TAX = "tax", "Tax"
        UTILITY = "utility", "Utility"
        PROPERTY_TAX = "property_tax", "Property Tax"
        WATER_TAX = "water_tax", "Water Tax"
        EB_DEPOSIT = "eb_deposit", "EB Deposit"
        OTHER = "other", "Other"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="transactions")
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    transaction_date = models.DateField()
    paid_by = models.CharField(max_length=20, choices=PaidBy.choices, default=PaidBy.OWNER)
    payment_mode = models.CharField(max_length=30, blank=True)
    reference_number = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_transactions")

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} - {self.amount}"


class UtilityRecord(TimeStampedModel):
    class UtilityType(models.TextChoices):
        EB = "eb", "Electricity"
        WATER = "water", "Water"
        GAS = "gas", "Gas"
        COMMON_AREA = "common_area", "Common Area"

    class BillingModel(models.TextChoices):
        METERED = "metered", "Metered"
        FIXED = "fixed", "Fixed"
        SHARED = "shared", "Shared"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="utility_records")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="utility_records")
    utility_type = models.CharField(max_length=20, choices=UtilityType.choices)
    billing_model = models.CharField(max_length=20, choices=BillingModel.choices, default=BillingModel.METERED)
    meter_number = models.CharField(max_length=100, blank=True)
    previous_reading = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_reading = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consumption_units = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate_per_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bill_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.billing_model == self.BillingModel.METERED:
            self.consumption_units = max(self.current_reading - self.previous_reading, 0)
            self.bill_amount = self.consumption_units * self.rate_per_unit
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.unit} - {self.get_utility_type_display()}"


def document_upload_to(instance, filename: str) -> str:
    module = instance.module_type or "owner"
    property_id = instance.property_id or "unassigned"
    tenant_id = instance.tenant_id or "no-tenant"
    return f"{module}/{property_id}/{tenant_id}/{filename}"


class Document(TimeStampedModel):
    class ModuleType(models.TextChoices):
        COMMERCIAL = "commercial", "Commercial"
        RESIDENTIAL = "residential", "Residential"
        OWNER = "owner", "Owner"

    class DocumentType(models.TextChoices):
        AGREEMENT = "agreement", "Agreement"
        AADHAR = "aadhar", "Aadhar"
        PAN = "pan", "PAN"
        GST = "gst", "GST"
        LICENSE = "license", "License"
        RECEIPT = "receipt", "Receipt"
        INVOICE = "invoice", "Invoice"
        TAX = "tax", "Tax"
        EB_BILL = "eb_bill", "EB Bill"
        PROPERTY_TAX_RECEIPT = "property_tax_receipt", "Property Tax Receipt"
        WATER_TAX_RECEIPT = "water_tax_receipt", "Water Tax Receipt"
        OTHER = "other", "Other"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="documents")
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    module_type = models.CharField(max_length=20, choices=ModuleType.choices)
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file = models.FileField(upload_to=document_upload_to)
    original_file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_documents")

    def __str__(self) -> str:
        return self.original_file_name


class RentLedger(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="rent_ledger")
    period_month = models.PositiveIntegerField()  # 1–12
    period_year = models.PositiveIntegerField()
    due_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("tenant", "period_month", "period_year")
        ordering = ["-period_year", "-period_month"]

    @property
    def pending_amount(self):
        return max(self.due_amount - self.paid_amount, 0)

    def __str__(self) -> str:
        return f"{self.tenant} — {self.period_month}/{self.period_year}"


class DepositLedger(TimeStampedModel):
    class EntryType(models.TextChoices):
        RECEIVED = "received", "Received"
        ADJUSTED = "adjusted", "Adjusted"
        REFUNDED = "refunded", "Refunded"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="deposit_ledger")
    entry_type = models.CharField(max_length=20, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    date = models.DateField()
    linked_transaction = models.ForeignKey(
        "Transaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="deposit_entries"
    )

    class Meta:
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.tenant} — {self.get_entry_type_display()} ₹{self.amount}"


def receipt_upload_to(instance, filename: str) -> str:
    return f"receipts/{instance.receipt_number}/{filename}"


class Receipt(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATED = "generated", "Generated"
        FAILED = "failed", "Failed"

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=50, unique=True)
    receipt_date = models.DateField()
    file = models.FileField(upload_to=receipt_upload_to, blank=True)
    generation_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self) -> str:
        return self.receipt_number


class ActivityLog(TimeStampedModel):
    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        VIEW = "view", "View"
        PAYMENT = "payment", "Payment"
        EXPORT = "export", "Export"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="activity_logs"
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=50, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.action} — {self.resource_type}"
