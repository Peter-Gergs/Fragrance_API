from django.contrib import admin
from .models import Order, OrderItem, ShippingSetting, PendingOrder


# ✅ OrderItem Inline للعرض في صفحة الطلب
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # نعتمد على دالة display_variant لعرض المنتج والـ Variant
    readonly_fields = ["display_variant", "quantity", "price"]
    fields = ["display_variant", "quantity", "price"]

    def display_variant(self, obj):
        product_name = None
        details = ""

        # جرب تجيب اسم المنتج من العلاقة أو من الحقل name
        if obj.product:
            product_name = obj.product.name
        elif obj.name:
            product_name = obj.name

        # جرب تجيب تفاصيل الـ variant (الحجم مثلًا)
        if obj.variant:
            size = getattr(obj.variant, "size_ml", None)
            if size:
                details = f"{size} ml"

        # fallback في حالة مفيش أي بيانات
        if not product_name:
            return "—"

        return f"{product_name} ({details})".strip()

    display_variant.short_description = "Product/Variant (ml)"


# ✅ تحسين شكل عرض الطلبات في لوحة الأدمن
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_user_fullname",  # يعرض الاسم الكامل أو اسم العميل الضيف
        "customer_phone",
        "city",
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
    # ... (بقية الحقول)

    # ✅ دالة مخصصة لعرض اسم العميل (مسجل أو ضيف)
    def get_user_fullname(self, obj):
        if obj.user and obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        if obj.username:
            return obj.username
        return "Guest"

    get_user_fullname.short_description = "Customer Name"
    search_fields = [
        "user__username",
        "customer_phone",
        "city",
        "username",
    ]  # ✅ إضافة username للبحث
    inlines = [OrderItemInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("user", "total_amount")
        return self.readonly_fields


@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display = ("governorate", "cost")
    search_fields = ("governorate",)
    list_editable = ("cost",)


# ✅ التسجيل في الأدمن
admin.site.register(Order, OrderAdmin)
admin.site.register(PendingOrder)
