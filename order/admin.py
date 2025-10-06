from django.contrib import admin
from .models import Order, OrderItem, ShippingSetting, PendingOrder


# ✅ OrderItem Inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["display_variant", "quantity", "price"]
    fields = ["display_variant", "quantity", "price"]

    def display_variant(self, obj):
        product_name = None
        details = ""

        if obj.product:
            product_name = obj.product.name
        elif obj.name:
            product_name = obj.name

        if obj.variant:
            size = getattr(obj.variant, "size_ml", None)
            if size:
                details = f"{size} ml"

        if not product_name:
            return "—"

        return f"{product_name} ({details})".strip()

    display_variant.short_description = "Product/Variant (ml)"


# ✅ تحسين عرض الطلبات
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_user_fullname",
        "customer_phone",
        "city",
        "get_shipping_cost",  # 👈 أضفنا عمود تكلفة الشحن
        "total_amount",
        "payment_status",
        "order_status",
        "created_at",
    ]
    list_filter = [
        "payment_status",
        "order_status",
        "city",
    ]
    search_fields = [
        "user__username",
        "customer_phone",
        "city",
        "username",
    ]
    inlines = [OrderItemInline]

    def get_user_fullname(self, obj):
        if obj.user and obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        if obj.username:
            return obj.username
        return "Guest"

    get_user_fullname.short_description = "Customer Name"

    # ✅ دالة جديدة لحساب تكلفة الشحن من الـ ShippingSetting
    def get_shipping_cost(self, obj):
        try:
            shipping = ShippingSetting.objects.get(governorate=obj.governorate)
            return f"{shipping.cost} EGP"
        except ShippingSetting.DoesNotExist:
            return "—"

    get_shipping_cost.short_description = "Shipping Cost"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("user", "total_amount")
        return self.readonly_fields


@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display = ("governorate", "cost")
    search_fields = ("governorate",)
    list_editable = ("cost",)


admin.site.register(Order, OrderAdmin)
