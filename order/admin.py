from django.contrib import admin
from .models import Order, OrderItem, ShippingSetting, PendingOrder


# ✅ عشان نشوف الطلبات الفرعية داخل كل طلب
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = [
        "product",
        "name",
        "quantity",
        "price",
    ]  # 🔹 خلتهم للعرض فقط (اختياري)


# ✅ تحسين شكل عرض الطلبات في لوحة الأدمن
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_user_fullname",
        "user",
        "customer_phone",
        "city",
        "total_amount",
        "payment_status",
        "order_status",
        "created_at",
    ]  # 🔹 دول الأعمدة اللي هتظهر قدامك في جدول الطلبات
    list_filter = [
        "payment_status",
        "order_status",
        "city",
    ]  # 🔹 فلترة الطلبات حسب الحالات
    fields = [
        "user",  # 👈 نحطه أول واحد
        "customer_phone",
        "governorate",
        "city",
        "street",
        "building_number",
        "floor_number",
        "apartment_number",
        "landmark",
        "total_amount",
        "payment_status",
        "order_status",
    ]

    def get_user_fullname(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    get_user_fullname.short_description = "Customer Name"
    search_fields = ["user__username", "customer_phone", "city"]  # 🔹 البحث السريع
    inlines = [OrderItemInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # يعني في حالة التعديل مش الإنشاء
            return self.readonly_fields + ("user", "total_amount")
        return self.readonly_fields


@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display = ("governorate", "cost")
    search_fields = ("governorate",)
    list_editable = ("cost",)  # 🔹 يسمح بتعديل تكلفة الشحن مباشرة من الجدول


# ✅ التسجيل في الأدمن
admin.site.register(Order, OrderAdmin)
admin.site.register(PendingOrder)
