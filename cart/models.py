from django.db import models
from django.contrib.auth.models import User
from product.models import ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({self.user.username})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return (
            f"{self.variant.product.name} - {self.variant.size_ml}ml (x{self.quantity})"
        )


