from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    short_description = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    image = models.ImageField(upload_to="category_images/", blank=True, null=True)
    is_special = models.BooleanField(default=False)
    special_title = models.CharField(max_length=100, blank=True, null=True)
    special_description = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200, unique=False, blank=False)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(max_length=1000, blank=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )
    brand = models.CharField(max_length=50, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    addedBy = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    priority = models.PositiveIntegerField(default=1)  

    class Meta:
        ordering = ["priority", "-id"]  

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    size_ml = models.PositiveIntegerField()  # حجم الزجاجة بالملي
    price = models.DecimalField(max_digits=7, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    discount = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    withbox = models.BooleanField(default=False)
    travelsize = models.BooleanField(default=False)
    caption = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["size_ml"]

    def __str__(self):
        return f"{self.product.name} - {self.size_ml}ml"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="product_images/")
    alt_text = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class OfferImage(models.Model):
    image = models.ImageField(
        upload_to="offers/slider/simple/", verbose_name="صورة العرض"
    )

    class Meta:
        verbose_name_plural = "Offer Images"
        ordering = ["id"]

    def __str__(self):
        return f"صورة عرض #{self.id}"


class ReviewsImage(models.Model):
    image = models.ImageField(
        upload_to="reviews/slider/simple/", verbose_name="صورة التقييم"
    )

    class Meta:
        verbose_name_plural = "Reviews Images"
        ordering = ["id"]

    def __str__(self):
        return f"صورة عرض #{self.id}"
