from rest_framework import serializers
from .models import Cart, CartItem
from product.serializers import ProductSerializer, ProductVariantSerializer
from offers.services import OfferService


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
    discount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "created_at",
            "subtotal",
            "discount",
            "total",
            "items",
            "offers",
        ]

    def get_subtotal(self, obj):
        return OfferService().calculate(obj)["subtotal"]

    def get_discount(self, obj):
        return OfferService().calculate(obj)["discount"]

    def get_total(self, obj):
        return OfferService().calculate(obj)["total"]

    def get_offers(self, obj):
        return OfferService().calculate(obj)["offers"]
