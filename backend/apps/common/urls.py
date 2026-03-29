from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.common.views import (
    ActivityLogListView,
    AdminBackupView,
    AdminResetDataView,
    AdminUserDetailView,
    CurrentUserAPIView,
    DepositLedgerViewSet,
    DocumentViewSet,
    ForgotPasswordAPIView,
    LoginAPIView,
    LogoutAPIView,
    PropertyViewSet,
    ReceiptViewSet,
    RegisterAPIView,
    RentLedgerViewSet,
    ResetPasswordAPIView,
    TenantViewSet,
    TransactionViewSet,
    UnitViewSet,
    UserAdminListView,
    UtilityRecordViewSet,
)

router = DefaultRouter()
router.register("properties", PropertyViewSet, basename="property")
router.register("units", UnitViewSet, basename="unit")
router.register("tenants", TenantViewSet, basename="tenant")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("utilities", UtilityRecordViewSet, basename="utility")
router.register("documents", DocumentViewSet, basename="document")
router.register("receipts", ReceiptViewSet, basename="receipt")
router.register("rent-ledger", RentLedgerViewSet, basename="rent-ledger")
router.register("deposit-ledger", DepositLedgerViewSet, basename="deposit-ledger")

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="auth-register"),
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/me/", CurrentUserAPIView.as_view(), name="auth-me"),
    path("auth/forgot-password/", ForgotPasswordAPIView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password/", ResetPasswordAPIView.as_view(), name="auth-reset-password"),
    path("admin/activity-logs/", ActivityLogListView.as_view(), name="activity-logs"),
    path("admin/users/", UserAdminListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/backup/", AdminBackupView.as_view(), name="admin-backup"),
    path("admin/reset-data/", AdminResetDataView.as_view(), name="admin-reset-data"),
]

urlpatterns += router.urls
