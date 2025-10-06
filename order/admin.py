from django.contrib import admin
from django.utils.html import format_html
from django.db.models import fields
from .models import Order, OrderItem, ShippingSetting, PendingOrder


# ✅ OrderItem Inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["display_image", "display_variant", "quantity", "price"]
    fields = ["display_image", "display_variant", "quantity", "price"]

    def display_image(self, obj):
        image_url = None
        if obj.product and obj.product.images.first():
            image_url = obj.product.images.first().image.url

        if image_url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />',
                image_url,
            )
        return format_html("—")

    display_image.short_description = "Image"

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
        "get_shipping_cost",
        "calculate_final_total",
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

    # الحقول التي لا نريد أن تكون للقراءة فقط أبداً
    exclude_from_readonly = ["order_status"]

    def get_user_fullname(self, obj):
        if obj.user and obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        if obj.username:
            return obj.username
        return "Guest"

    get_user_fullname.short_description = "Customer Name"

    # دالة لحساب تكلفة الشحن (EGP)
    def get_actual_shipping_cost(self, obj):
        try:
            shipping = ShippingSetting.objects.get(governorate=obj.governorate)
            return shipping.cost
        except ShippingSetting.DoesNotExist:
            return 0.0

    # دالة لعرض تكلفة الشحن في قائمة OrderAdmin
    def get_shipping_cost(self, obj):
        cost = self.get_actual_shipping_cost(obj)
        if cost > 0:
            return f"{cost} EGP"
        return "—"

    get_shipping_cost.short_description = "Shipping Cost"

    # دالة لحساب الإجمالي الكلي (المنتجات + الشحن)
    def calculate_final_total(self, obj):
        shipping_cost = self.get_actual_shipping_cost(obj)
        final_total = obj.total_amount + shipping_cost
        return f"{final_total:.2f} EGP"

    calculate_final_total.short_description = "Total Final (Incl. Ship.)"
    calculate_final_total.admin_order_field = "total_amount"

    # ✅ دالة get_readonly_fields المصححة
    def get_readonly_fields(self, request, obj=None):
        if obj:
            # 1. نحصل على جميع الحقول والعلاقات للموديل
            # 2. نستثني الحقول التي تم إنشاؤها تلقائياً (مثل العلاقات العكسية) ما لم تكن علاقة OneToOne
            all_fields = [
                f.name
                for f in self.model._meta.get_fields()
                if not f.auto_created or f.one_to_one
            ]

            # 3. نحصل على الحقول التي يجب أن تكون للقراءة فقط (كل الحقول باستثناء 'id' و 'order_status')
            readonly = [
                f
                for f in all_fields
                if f not in self.exclude_from_readonly and f != "id"
            ]

            # 4. نضمن أن الحقول المحسوبة (الـ methods) للقراءة فقط مُضمنة أيضاً
            computed_readonly = [
                "get_user_fullname",
                "get_shipping_cost",
                "calculate_final_total",
                "display_image",
            ]

            return tuple(set(readonly) | set(computed_readonly))

        return self.readonly_fields


@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display = ("governorate", "cost")
    search_fields = ("governorate",)
    list_editable = ("cost",)


admin.site.register(Order, OrderAdmin)
admin.site.register(PendingOrder)
