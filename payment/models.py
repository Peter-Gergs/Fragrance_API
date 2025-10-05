from django.db import models
from cart.models import Cart


class PaymentTransaction(models.Model):
    """
    يخزن مرجع OPay ومعلومات الشحن بشكل دائم بدلاً من الاعتماد على الـ Session.
    """

    # مرجع OPay الفريد اللي بيستخدم للـ Webhook
    opay_reference = models.CharField(max_length=100, unique=True, db_index=True)

    # ربطها بالكارت اللي تم الدفع عشانه
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True)

    # تخزين بيانات العميل والشحن كـ JSON
    checkout_address_json = models.JSONField(default=dict)

    # حالة العملية
    status = models.CharField(max_length=20, default="PENDING")

    # وقت الإنشاء
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OPay Ref: {self.opay_reference} - Status: {self.status}"
