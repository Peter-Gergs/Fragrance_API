from django.contrib import admin
from django.utils.html import format_html
from django.db.models import fields

# استيراد النماذج (Models)
from .models import Order, OrderItem, ShippingSetting, PendingOrder


# ====================================================================
# 1. OrderItem Inline (لإظهار المنتجات داخل صفحة الطلب)
# ====================================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # ✅ إضافة الصورة هنا فقط، مع بقية الحقول للقراءة فقط
    readonly_fields = ["display_image", "display_variant", "quantity", "price"]
    fields = ["display_image", "display_variant", "quantity", "price"]

    # ✅ دالة عرض الصورة في الـ Inline
    def display_image(self, obj):
        image_url = None
        # افتراض أن المنتج لديه علاقة 'images' وأن الصورة الأولى هي الرئيسية
        if obj.product and obj.product.images.first():
            image_url = obj.product.images.first().image.url

        if image_url:
            # عرض الصورة بحجم صغير ومناسب
            return format_html(
                '<img src="{}" style="width: 75px; height: 80px; object-fit: cover;" />',
                image_url,
            )
        return format_html("—")

    display_image.short_description = "Image"

    # دالة عرض اسم المنتج والتفاصيل
    def display_variant(self, obj):
        product_name = None
        details = ""
        # ... (بقية منطق عرض المنتج كما كان)
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


# ====================================================================
# 2. Order Admin (لوحة تحكم الطلبات)
# ====================================================================
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_user_fullname",
        "customer_phone",
        "city",
        "get_shipping_cost",
        "calculate_final_total",
        "remaining_amount",  # <-- الحقل الجديد
        "payment_status",
        "order_status",
        "created_at",
    ]
    list_filter = ["payment_status", "order_status", "city"]
    search_fields = ["user__username", "customer_phone", "city", "username"]
    inlines = [OrderItemInline]
    exclude_from_readonly = ["order_status"]

    fields = (
        "payment_status",
        "order_status",
        "get_user_fullname",
        "customer_phone",
        "governorate",
        "calculate_final_total",
        "remaining_amount",  # <-- الحقل الجديد
        "get_shipping_cost",
        "total_amount",
        "city",
        "street",
        "building_number",
        "floor_number",
        "apartment_number",
        "username",
        "created_at",
        "landmark",
        "user",
    )

    # دوال موجودة
    def get_user_fullname(self, obj):
        if obj.user and obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        if obj.username:
            return obj.username
        return "Guest"

    get_user_fullname.short_description = "Customer Name"

    def get_actual_shipping_cost(self, obj):
        try:
            shipping = ShippingSetting.objects.get(governorate=obj.governorate)
            return shipping.cost
        except ShippingSetting.DoesNotExist:
            return 0.0

    def get_shipping_cost(self, obj):
        cost = self.get_actual_shipping_cost(obj)
        if cost > 0:
            return f"{cost} EGP"
        return "—"

    get_shipping_cost.short_description = "Shipping Cost"

    def calculate_final_total(self, obj):
        shipping_cost = self.get_actual_shipping_cost(obj)
        final_total = obj.total_amount + shipping_cost
        return f"{final_total:.2f} EGP"

    calculate_final_total.short_description = "Total Final (Incl. Ship.)"
    calculate_final_total.admin_order_field = "total_amount"

    # الحقل الجديد
    def remaining_amount(self, obj):
        if obj.payment_status.lower() == "cash":
            remaining = obj.total_amount - 100
            return f"{remaining:.2f} EGP"
        return "—"

    remaining_amount.short_description = "Remaining Amount"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            all_fields = [
                f.name
                for f in self.model._meta.get_fields()
                if not f.auto_created or f.one_to_one
            ]
            readonly = [
                f
                for f in all_fields
                if f not in self.exclude_from_readonly and f != "id"
            ]
            computed_readonly = [
                "get_user_fullname",
                "get_shipping_cost",
                "calculate_final_total",
                "remaining_amount",  # <-- خليها readonly
            ]
            return tuple(set(readonly) | set(computed_readonly))
        return self.readonly_fields


# ====================================================================
# 3. تسجيل النماذج
# ====================================================================


@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display = ("governorate", "cost")
    search_fields = ("governorate",)
    list_editable = ("cost",)


admin.site.register(Order, OrderAdmin)
