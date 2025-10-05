from django.db import models
from operator import mod
from django.contrib.auth.models import User
from product.models import Product

# Create your models here.


class OrderStatus(models.TextChoices):
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"


class PaymentStatus(models.TextChoices):
    PAID = "Paid"
    UNPAID = "Unpaid"


class Order(models.Model):
    # معلومات العميل
    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="orders"
    )
    customer_phone = models.CharField(max_length=20)

    # Address
    governorate = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=100)
    building_number = models.CharField(max_length=20, blank=True, null=True)
    floor_number = models.CharField(max_length=20, blank=True, null=True)
    apartment_number = models.CharField(max_length=20, blank=True, null=True)
    landmark = models.CharField(max_length=100, blank=True, null=True)

    # order details
    total_amount = models.IntegerField(default=0)
    payment_status = models.CharField(
        max_length=30, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    order_status = models.CharField(
        max_length=30, choices=OrderStatus.choices, default=OrderStatus.PROCESSING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    # معلومات العميل
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    order = models.ForeignKey(
        Order, null=True, on_delete=models.CASCADE, related_name="orderitems"
    )
    name = models.CharField(max_length=200, default="", blank=False)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=7, decimal_places=2, blank=False)

    def __str__(self):
        return self.name


class ShippingSetting(models.Model):
    governorate = models.CharField(max_length=100, unique=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=60.00)

    def __str__(self):
        return f"Shipping Cost: {self.cost} EGP"


class PendingOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer_phone = models.CharField(max_length=20, blank=True)
    governorate = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    street = models.CharField(max_length=255, blank=True)
    building_number = models.CharField(max_length=10, blank=True)
    floor_number = models.CharField(max_length=10, blank=True)
    apartment_number = models.CharField(max_length=10, blank=True)
    landmark = models.CharField(max_length=255, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paymob_order_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PendingOrder #{self.id} - {self.user.username}"
