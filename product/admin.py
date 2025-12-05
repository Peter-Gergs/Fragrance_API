from django.contrib import admin, messages
from django.forms import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.utils.translation import activate
from .models import Product, ProductImage, Category, ProductVariant,OfferImage
from django.utils.html import format_html


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
    fields = ["size_ml", "withbox", "travelsize", "price", "stock", "discount"]


# --- Product Admin ---
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "id", "brand", "get_category"]
    inlines = [ProductImageInline, ProductVariantInline]
    ordering = ("-id",)  

    def get_category(self, obj):
        return obj.category.name if obj.category else "-"

    get_category.short_description = "Category"


# --- Register models ---
admin.site.register(Product, ProductAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_special", "preview_image")
    list_filter = ("is_special",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("preview_image",)
    fieldsets = (
        (
            "Basic Info",
            {"fields": ("name", "slug", "short_description", "image", "preview_image")},
        ),
        (
            "Special Section",
            {
                "fields": ("is_special", "special_title", "special_description"),
                "classes": ("collapse",),
            },
        ),
    )

    def preview_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="100" style="border-radius:8px" />'
            )
        return "No image"

    preview_image.short_description = "Preview"


admin.site.register(Category, CategoryAdmin)

# Custom Admin Site
admin.site.site_header = "3S Fragrance"


class MyAdminSite(admin.AdminSite):
    def each_context(self, request):
        activate("en")  # Force English
        return super().each_context(request)


admin_site = MyAdminSite(name="myadmin")


@admin.register(OfferImage)
class OfferImageAdmin(admin.ModelAdmin):
    # ✅ الحقول التي تظهر في قائمة العروض (ID والصورة المصغرة فقط)
    list_display = ("id", "display_image_thumbnail")

    # ❌ لا يوجد list_editable

    # ✅ الحقول التي تظهر في صفحة إضافة/تعديل العرض (حقل الصورة فقط)
    fields = ("image",)

    # ✅ دالة لعرض الصورة المصغرة في قائمة العروض
    def display_image_thumbnail(self, obj):
        if obj.image:
            # عرض الصورة بحجم صغير (50x50 بكسل)
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url,
            )
        return "—"

    display_image_thumbnail.short_description = "صورة العرض"
