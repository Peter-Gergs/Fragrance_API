from django.contrib import admin, messages
from django.forms import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.utils.translation import activate

from .models import Product, ProductImage, Category, ProductVariant


# --- Inline for product images ---
class ProductImageInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total_images = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                image = form.cleaned_data.get("image")
                if image:
                    total_images += 1
        if total_images == 0:
            raise ValidationError("You must add at least one image for the product.")
        if total_images > 6:
            raise ValidationError("You can't add more than 6 images.")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    formset = ProductImageInlineFormset
    extra = 1
    max_num = 6

    def preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="100" style="border-radius:5px" />'
            )
        return ""

    readonly_fields = ["preview"]
    fields = ["image", "alt_text", "preview"]
    preview.short_description = "Preview"


# --- Inline for product variants ---
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ["size_ml", "price", "stock", "discount"]


# --- Product Admin ---
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "id", "brand", "get_category"]
    inlines = [ProductImageInline, ProductVariantInline]

    def get_category(self, obj):
        return obj.category.name if obj.category else "-"

    get_category.short_description = "Category"


# --- Register models ---
admin.site.register(Product, ProductAdmin)
admin.site.register(Category)

# Custom Admin Site
admin.site.site_header = "3S Fragrance"


class MyAdminSite(admin.AdminSite):
    def each_context(self, request):
        activate("en")  # Force English
        return super().each_context(request)


admin_site = MyAdminSite(name="myadmin")
