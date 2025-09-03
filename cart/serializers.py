from rest_framework import serializers
from .models import Cart, CartItem
from product.serializers import ProductSerializer, ProductVariantSerializer




class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "variant", "quantity"]

    def get_product(self, obj):
        return ProductSerializer(obj.variant.product).data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "created_at",
            "subtotal",
            "items",
        ]
    def get_subtotal(self, obj):
        total = 0
        for item in obj.items.all():
            # final_price من الـ variant مش من الـ product
            final_price = float(item.variant.price) - float(item.variant.discount or 0)
            total += final_price * item.quantity
        return format(total, ".2f")

    
