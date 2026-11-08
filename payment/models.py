from django.db import models
from cart.models import Cart


class PaymentTransaction(models.Model):
    """
    يخزن مرجع OPay ومعلومات الشحن بشكل دائم بدلاً من الاعتماد على الـ Session.
    """

    # مرجع OPay الفريد اللي بيستخدم للـ Webhook
    opay_reference = models.CharField(max_length=255, unique=True, db_index=True)

    # ربطها بالكارت اللي تم الدفع عشانه
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True)

    # تخزين بيانات العميل والشحن كـ JSON
    checkout_address_json = models.JSONField(default=dict)
    checkout_snapshot = models.JSONField(default=dict)
    receipt_token = models.CharField(max_length=64, unique=True, null=True, blank=True)

    # حالة العملية
    status = models.CharField(max_length=100, default="PENDING")

    # وقت الإنشاء
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OPay Ref: {self.opay_reference} - Status: {self.status}"
