from django.db import models


class Offer(models.Model):

    SIZE_CHOICES = (
        (3, "3 ml"),
        (6, "6 ml"),
        (10, "10 ml"),
        (30, "30 ml"),
    )

    title = models.CharField(max_length=100)

    size_ml = models.PositiveIntegerField(choices=SIZE_CHOICES)

    required_quantity = models.PositiveIntegerField()

    gift_quantity = models.PositiveIntegerField(default=0)

    original_price = models.DecimalField(max_digits=8, decimal_places=2)

    offer_price = models.DecimalField(max_digits=8, decimal_places=2)

    active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=1)  # <-- الجديد

    image = models.ImageField(upload_to="offers/specials", verbose_name="صورة العرض")

    start_date = models.DateField(null=True, blank=True)

    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
