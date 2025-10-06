from django.contrib import admin
from .models import Order, OrderItem, ShippingSetting, PendingOrder
from django.db.models import fields


from django.contrib import admin
from django.utils.html import format_html  # 👈 استيراد format_html
from django.db.models import fields
from .models import Order, OrderItem, ShippingSetting, PendingOrder


# ✅ OrderItem Inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # 👈 إضافة 'display_image' إلى readonly_fields
    readonly_fields = ["display_image", "display_variant", "quantity", "price"]
    # 👈 إضافة 'display_image' إلى fields
    fields = ["display_image", "display_variant", "quantity", "price"]

    # 1. دالة جديدة لعرض الصورة
    def display_image(self, obj):
        image_url = None
        if obj.product and obj.product.images.first():
            # نفترض أن المنتج (Product) لديه علاقة 'images' وأن الصورة الأولى هي الرئيسية
            image_url = obj.product.images.first().image.url

        if image_url:
            # نستخدم format_html لعرض الصورة بحجم مناسب (مثلاً 50x50 بكسل)
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />',
                image_url,
            )
        return format_html("—")

    display_image.short_description = "Image"

    # 2. الدالة الموجودة لديك لعرض اسم المنتج والتفاصيل
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


# ... بقية كلاس OrderAdmin وبقية الكود
# ... OrderAdmin, ShippingSettingAdmin, admin.site.register(Order, OrderAdmin)


# ✅ تحسين عرض الطلبات
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_user_fullname",
        "customer_phone",
        "city",
        "get_shipping_cost",
        "calculate_final_total",  # 👈 استخدام الدالة الجديدة للإجمالي
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

    # الحقول التي لا نريد أن تكون للقراءة فقط أبداً (لتسهيل التعديل في عرض الإضافة)
    exclude_from_readonly = ["order_status"]

    def get_user_fullname(self, obj):
        if obj.user and obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        if obj.username:
            return obj.username
        return "Guest"

    get_user_fullname.short_description = "Customer Name"

    # ✅ دالة لحساب تكلفة الشحن (EGP)
    def get_actual_shipping_cost(self, obj):
        """يحصل على تكلفة الشحن كرقم، أو 0 إذا لم يتم العثور عليها."""
        try:
            shipping = ShippingSetting.objects.get(governorate=obj.governorate)
            return shipping.cost
        except ShippingSetting.DoesNotExist:
            return 0.0

    # ✅ دالة لعرض تكلفة الشحن في قائمة OrderAdmin
    def get_shipping_cost(self, obj):
        cost = self.get_actual_shipping_cost(obj)
        if cost > 0:
            return f"{cost} EGP"
        return "—"

    get_shipping_cost.short_description = "Shipping Cost"

    # ✅ دالة لحساب الإجمالي الكلي (المنتجات + الشحن)
    def calculate_final_total(self, obj):
        shipping_cost = self.get_actual_shipping_cost(obj)
        final_total = obj.total_amount + shipping_cost
        return f"{final_total:.2f} EGP"

    calculate_final_total.short_description = "Total Final (Incl. Ship.)"
    # نجعلها قابلة للفرز بناءً على total_amount الحالية للموديل
    # إذا كانت لديك دالة لحساب الإجمالي الفعلي في الموديل، استخدمها هنا
    calculate_final_total.admin_order_field = "total_amount"

    # ✅ تعديل دالة get_readonly_fields لجعل كل شيء للقراءة فقط باستثناء 'order_status'
    def get_readonly_fields(self, request, obj=None):
        # إذا كان الكائن موجوداً (أي في صفحة تعديل وليس إضافة)
        if obj:
            # نحصل على جميع أسماء حقول الموديل (Model fields)
            all_fields = [
                f.name
                for f in self.model._meta.get_fields()
                if isinstance(f, (fields.Field, fields.ReverseRelation))
                and f.name != "id"
            ]

            # نستبعد الحقول التي نريد أن تكون قابلة للتعديل
            readonly = [f for f in all_fields if f not in self.exclude_from_readonly]

            # نضمن أن الحقول المحسوبة للقراءة فقط مُضمنة أيضاً
            computed_readonly = [
                "get_user_fullname",
                "get_shipping_cost",
                "calculate_final_total",
            ]

            return tuple(set(readonly) | set(computed_readonly))

        # عند إضافة طلب جديد، نعود للحقول القراءة فقط الافتراضية
        return self.readonly_fields


@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display = ("governorate", "cost")
    search_fields = ("governorate",)
    list_editable = ("cost",)


admin.site.register(Order, OrderAdmin)
admin.site.register(PendingOrder)
