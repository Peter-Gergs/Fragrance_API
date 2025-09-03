# from django.contrib import admin
# from django.contrib import admin
# from django.contrib.auth.models import User
# from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin


# # Register your models here.


# # اعمل نسخة مخصصة من UserAdmin
# class CustomUserAdmin(DefaultUserAdmin):
#     list_display = ("username", "email", "id", "first_name", "last_name", "is_staff")


# # شيل التسجيل الافتراضي وسجل النسخة الجديدة
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from order.models import OrderItem

from account.models import Profile
from cart.models import Cart, CartItem
from order.models import Order


# Inline: Cart Items
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


# Inline: Cart
class CartInline(admin.StackedInline):
    model = Cart
    extra = 0
    show_change_link = True


# Inline: Orders
class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    show_change_link = True


# Inline: Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    can_delete = False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["order", "product", "name", "quantity", "price"]
    readonly_fields = ["order", "product", "name", "quantity", "price"]
    can_delete = False

    def has_add_permission(self, request, obj):
        return False  # عشان ما يزودش OrderItems من الأدمن


# Custom UserAdmin
class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline, CartInline, OrderInline]


# Replace default User admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
