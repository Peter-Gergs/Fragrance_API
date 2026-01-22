from rest_framework import serializers
from .models import Product, ProductImage, ProductVariant, OfferImage
from decimal import Decimal, ROUND_DOWN


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text"]


class ProductVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "size_ml",
            "price",
            "withbox",
            "travelsize",
            "final_price",
            "discount",
            "stock",
            "caption",
        ]

    def get_final_price(self, obj):
        if obj.discount:
            price = Decimal(obj.price) - Decimal(obj.discount)
        else:
            price = Decimal(obj.price)
        return format(price.quantize(Decimal("0.00"), rounding=ROUND_DOWN), "f")


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "category",
            "brand",
            "min_price",
            "max_price",
            "variants",
            "images",
            "created_at",
        ]

    def get_min_price(self, obj):
        if not obj.variants.exists():
            return None
        prices = [
            float(variant.price) - float(variant.discount or 0)
            for variant in obj.variants.all()
        ]
        return round(min(prices), 2)

    def get_max_price(self, obj):
        if not obj.variants.exists():
            return None
        prices = [
            float(variant.price) - float(variant.discount or 0)
            for variant in obj.variants.all()
        ]
        return round(max(prices), 2)


class OfferImageSerializer(serializers.ModelSerializer):
    """مسلسل بسيط يعرض رابط الصورة فقط."""

    class Meta:
        model = OfferImage
        fields = ["id", "image"]  # ✅ نحتاج فقط إلى ID ورابط الصورة
