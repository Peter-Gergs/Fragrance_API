from django.db import models
from django.contrib.auth.models import User
from product.models import ProductVariant


class Cart(models.Model):
    # ممكن يبقى مربوط بيوزر أو بـ session
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Cart (User: {self.user.username})"
        return f"Cart (Session: {self.session_key})"


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
        if self.variant:
            return f"{self.variant.product.name} - {self.variant.size_ml}ml (x{self.quantity})"
        return f"CartItem (No Variant)"
