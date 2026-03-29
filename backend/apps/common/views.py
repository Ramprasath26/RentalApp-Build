from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
import datetime
from decimal import Decimal

from rest_framework import permissions, status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


class AuthRateThrottle(AnonRateThrottle):
    """Strict rate limit for auth endpoints — 5 requests/minute."""
    scope = "auth"

from apps.common.activity import log_activity
from apps.common.auth_serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserPublicSerializer,
)
from apps.common.models import ActivityLog, DepositLedger, Document, Property, Receipt, RentLedger, Tenant, Transaction, Unit, UtilityRecord
from apps.common.serializers import (
    ActivityLogSerializer,
    DepositLedgerSerializer,
    DocumentSerializer,
    PropertySerializer,
    ReceiptSerializer,
    RentLedgerSerializer,
    RentPaymentSerializer,
    TenantSerializer,
    TransactionSerializer,
    UnitSerializer,
    UserAdminSerializer,
    UtilityRecordSerializer,
)

User = get_user_model()


class QueryParamFilterMixin:
    filterset = {}

    def get_queryset(self):
        queryset = super().get_queryset()
        for param, lookup in self.filterset.items():
            value = self.request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{lookup: value})
        return queryset


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserPublicSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        log_activity(user, "login", request=request)
        return Response(
            {
                "token": token.key,
                "user": UserPublicSerializer(user).data,
            }
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        log_activity(request.user, "logout", request=request)
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Logged out successfully."})


class CurrentUserAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserPublicSerializer(request.user).data)


class ForgotPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()
        if user:
            token_generator = PasswordResetTokenGenerator()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_link = f"{settings.FRONTEND_BASE_URL}/?mode=reset&uid={uid}&token={token}"

            send_mail(
                subject="Reset your RentalApp-Build password",
                message=(
                    "You requested a password reset for RentalApp-Build.\n\n"
                    f"Use this link to reset your password:\n{reset_link}\n\n"
                    "If you did not request this, please ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        # Security: never return token/uid in response — only send via email
        return Response({"detail": "If an account exists, a reset link has been sent."})


class ResetPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"detail": "Invalid password reset link."}, status=status.HTTP_400_BAD_REQUEST)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"detail": "Password reset token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        new_token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "detail": "Password has been reset successfully.",
                "token": new_token.key,
                "user": UserPublicSerializer(user).data,
            }
        )


class PropertyViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = Property.objects.select_related("owner").all().order_by("name")
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {"owner": "owner_id", "property_type": "property_type"}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class UnitViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = Unit.objects.select_related("property").all().order_by("property__name", "unit_code")
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {"property": "property_id", "module_type": "module_type", "status": "status"}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(property__owner=self.request.user)


class TenantViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = Tenant.objects.select_related("unit", "unit__property").all().order_by("display_name")
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {"unit": "unit_id", "tenant_type": "tenant_type", "status": "status"}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(unit__property__owner=self.request.user)


class TransactionViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related("property", "unit", "tenant", "created_by").all().order_by("-transaction_date", "-created_at")
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {
        "property": "property_id",
        "unit": "unit_id",
        "tenant": "tenant_id",
        "transaction_type": "transaction_type",
        "category": "category",
    }

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(property__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class UtilityRecordViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = UtilityRecord.objects.select_related("property", "unit").all().order_by("-billing_period_end")
    serializer_class = UtilityRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {"property": "property_id", "unit": "unit_id", "utility_type": "utility_type", "payment_status": "payment_status"}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(property__owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        record = self.get_object()
        paid_amount = request.data.get("paid_amount", record.bill_amount)
        try:
            paid_amount = Decimal(str(paid_amount))
        except Exception:
            return Response({"detail": "Invalid paid_amount."}, status=status.HTTP_400_BAD_REQUEST)

        record.paid_amount = paid_amount
        if paid_amount >= record.bill_amount:
            record.payment_status = UtilityRecord.PaymentStatus.PAID
        elif paid_amount > 0:
            record.payment_status = UtilityRecord.PaymentStatus.PARTIAL
        record.save(update_fields=["paid_amount", "payment_status"])
        return Response(UtilityRecordSerializer(record).data)


class DocumentViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = Document.objects.select_related("property", "unit", "tenant", "uploaded_by").all().order_by("-created_at")
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset = {
        "property": "property_id",
        "unit": "unit_id",
        "tenant": "tenant_id",
        "module_type": "module_type",
        "document_type": "document_type",
    }

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(property__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ReceiptViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = Receipt.objects.select_related("transaction").all().order_by("-receipt_date")
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {"transaction": "transaction_id", "generation_status": "generation_status"}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(transaction__property__owner=self.request.user)


class RentLedgerViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = RentLedger.objects.select_related("tenant", "tenant__unit").all()
    serializer_class = RentLedgerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {"tenant": "tenant_id", "period_year": "period_year", "period_month": "period_month", "status": "status"}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(tenant__unit__property__owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        ledger = self.get_object()
        serializer = RentPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        payment_mode = serializer.validated_data.get("payment_mode", "")
        notes = serializer.validated_data.get("notes", "")
        txn_date = serializer.validated_data.get("transaction_date") or datetime.date.today()

        # Record payment as a Transaction
        txn = Transaction.objects.create(
            property=ledger.tenant.unit.property,
            unit=ledger.tenant.unit,
            tenant=ledger.tenant,
            transaction_type=Transaction.TransactionType.INCOME,
            category=Transaction.Category.RENT,
            amount=amount,
            transaction_date=txn_date,
            payment_mode=payment_mode,
            notes=notes or f"Rent payment for {ledger.period_month}/{ledger.period_year}",
            created_by=request.user,
        )

        # Update ledger
        ledger.paid_amount = ledger.paid_amount + amount
        if ledger.paid_amount >= ledger.due_amount:
            ledger.status = RentLedger.Status.PAID
        else:
            ledger.status = RentLedger.Status.PARTIAL
        ledger.save()

        return Response(
            {
                "ledger": RentLedgerSerializer(ledger).data,
                "transaction_id": txn.id,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        """Generate and return a PDF rent receipt for this ledger entry."""
        from apps.common.receipt_generator import generate_rent_receipt
        ledger = self.get_object()
        tenant = ledger.tenant
        unit = tenant.unit
        prop = unit.property

        # Find the latest rent transaction for this ledger period
        txn = Transaction.objects.filter(
            tenant=tenant,
            category=Transaction.Category.RENT,
            transaction_date__year=ledger.period_year,
            transaction_date__month=ledger.period_month,
        ).order_by("-transaction_date").first()

        # Build receipt number
        receipt_no = f"RCP-{prop.id:03d}-{tenant.id:03d}-{ledger.period_year}{ledger.period_month:02d}"

        logo_path = None
        logo_candidate = settings.BASE_DIR.parent / "logo.png"
        if logo_candidate.exists():
            logo_path = str(logo_candidate)

        owner_name = (
            f"{prop.owner.first_name} {prop.owner.last_name}".strip()
            if hasattr(prop, "owner") and prop.owner else "Property Owner"
        )

        pdf_bytes = generate_rent_receipt(
            receipt_number=receipt_no,
            receipt_date=txn.transaction_date if txn else datetime.date.today(),
            tenant_name=tenant.display_name,
            tenant_phone=getattr(tenant, "phone", "") or "",
            property_name=prop.name,
            unit_code=unit.unit_code,
            period_month=ledger.period_month,
            period_year=ledger.period_year,
            rent_amount=float(ledger.due_amount),
            paid_amount=float(ledger.paid_amount),
            payment_mode=txn.payment_mode if txn else "cash",
            transaction_id=txn.id if txn else "—",
            owner_name=owner_name,
            logo_path=logo_path,
        )

        filename = f"{receipt_no}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class DepositLedgerViewSet(QueryParamFilterMixin, viewsets.ModelViewSet):
    queryset = DepositLedger.objects.select_related("tenant").all()
    serializer_class = DepositLedgerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset = {"tenant": "tenant_id", "entry_type": "entry_type"}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(tenant__unit__property__owner=self.request.user)

    @action(detail=False, methods=["get"], url_path="balance")
    def balance(self, request):
        tenant_id = request.query_params.get("tenant")
        if not tenant_id:
            return Response({"detail": "tenant query param required."}, status=status.HTTP_400_BAD_REQUEST)

        entries = DepositLedger.objects.filter(tenant_id=tenant_id)
        received = sum(e.amount for e in entries if e.entry_type == DepositLedger.EntryType.RECEIVED)
        adjusted = sum(e.amount for e in entries if e.entry_type == DepositLedger.EntryType.ADJUSTED)
        refunded = sum(e.amount for e in entries if e.entry_type == DepositLedger.EntryType.REFUNDED)
        balance = received - adjusted - refunded

        return Response(
            {
                "tenant_id": int(tenant_id),
                "received": received,
                "adjusted": adjusted,
                "refunded": refunded,
                "balance": balance,
            }
        )


class ActivityLogListView(ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = ActivityLog.objects.select_related("user").order_by("-created_at")
        user_id = self.request.query_params.get("user_id")
        action = self.request.query_params.get("action")
        if user_id:
            qs = qs.filter(user_id=user_id)
        if action:
            qs = qs.filter(action=action)
        return qs[:200]


class UserAdminListView(ListAPIView):
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all().order_by("-date_joined")


import json
from django.core import serializers as dj_serializers
from django.contrib.auth.hashers import make_password

class AdminUserDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        action_type = request.data.get("action")
        if action_type == "toggle_active":
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            log_activity(request.user, "update", "User", pk, f"Set is_active={target.is_active}", request)
            return Response({"id": target.pk, "is_active": target.is_active})

        if action_type == "reset_password":
            new_pw = request.data.get("new_password", "")
            if len(new_pw) < 6:
                return Response({"detail": "Password must be at least 6 characters."}, status=status.HTTP_400_BAD_REQUEST)
            target.set_password(new_pw)
            target.save(update_fields=["password"])
            Token.objects.filter(user=target).delete()
            log_activity(request.user, "update", "User", pk, f"Password reset for {target.username}", request)
            return Response({"detail": f"Password reset for {target.username}."})

        if action_type == "toggle_staff":
            if target == request.user:
                return Response({"detail": "Cannot change your own staff status."}, status=status.HTTP_400_BAD_REQUEST)
            target.is_staff = not target.is_staff
            target.save(update_fields=["is_staff"])
            return Response({"id": target.pk, "is_staff": target.is_staff})

        return Response({"detail": "Unknown action."}, status=status.HTTP_400_BAD_REQUEST)


class AdminBackupView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from apps.common.models import Property, Unit, Tenant, Transaction, UtilityRecord, RentLedger, DepositLedger
        data = {}
        for model in [Property, Unit, Tenant, Transaction, UtilityRecord, RentLedger, DepositLedger]:
            name = model.__name__
            data[name] = json.loads(dj_serializers.serialize("json", model.objects.all()))

        log_activity(request.user, "export", "Backup", "", "Full data backup downloaded", request)
        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type="application/json"
        )
        ts = datetime.date.today().strftime("%Y%m%d")
        response["Content-Disposition"] = f'attachment; filename="rentalapp-backup-{ts}.json"'
        return response


class AdminResetDataView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        confirm = request.data.get("confirm")
        if confirm != "DELETE ALL DATA":
            return Response(
                {"detail": "Send confirm='DELETE ALL DATA' to proceed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        from apps.common.models import Property, Unit, Tenant, Transaction, UtilityRecord, RentLedger, DepositLedger, Document, Receipt
        counts = {}
        for model in [Receipt, Document, DepositLedger, RentLedger, UtilityRecord, Transaction, Tenant, Unit, Property]:
            n, _ = model.objects.all().delete()
            counts[model.__name__] = n
        log_activity(request.user, "delete", "ResetData", "", f"All data deleted: {counts}", request)
        return Response({"detail": "All data has been deleted.", "counts": counts})
