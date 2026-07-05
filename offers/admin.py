from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "size_ml",
        "required_quantity",
        "offer_price",
        "active",
    )

    list_filter = (
        "size_ml",
        "active",
    )
