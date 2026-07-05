from decimal import Decimal
from .models import Offer


class OfferService:

    def calculate(self, cart):

        items = cart.items.select_related(
            "variant",
            "variant__product",
        )

        subtotal = Decimal("0")
        total = Decimal("0")
        discount = Decimal("0")

        grouped = {}

        # ===========================
        # Group items by size
        # ===========================

        for item in items:

            variant = item.variant

            item_price = Decimal(variant.price) - Decimal(variant.discount or 0)

            subtotal += item_price * item.quantity

            # المنتجات المستبعدة من العروض
            if not variant.product.allow_offer:
                total += item_price * item.quantity
                continue

            grouped.setdefault(variant.size_ml, []).append(
                {
                    "item": item,
                    "price": item_price,
                }
            )

        # ===========================
        # Apply Offers
        # ===========================
        applied_offers = []

        for size, products in grouped.items():

            quantity = sum(p["item"].quantity for p in products)

            offers = Offer.objects.filter(
                active=True,
                size_ml=size,
            ).order_by("-required_quantity")

            remaining = quantity

            # متوسط سعر القطعة (للباقي فقط)
            normal_price = (
                sum(p["price"] * p["item"].quantity for p in products) / quantity
            )

            for offer in offers:

                if remaining < offer.required_quantity:
                    continue

                count = remaining // offer.required_quantity
                applied_offers.append(
                    {
                        "id": offer.id,
                        "title": offer.title,
                        "size_ml": offer.size_ml,
                        "quantity": offer.required_quantity,
                        "times": count,
                        "offer_price": str(offer.offer_price),
                        "saved": str(
                            (Decimal(offer.original_price) - Decimal(offer.offer_price))
                            * count
                        ),
                    }
                )
                total += Decimal(offer.offer_price) * count

                remaining -= count * offer.required_quantity

            # المنتجات المتبقية تتحاسب عادي
            if remaining > 0:

                total += normal_price * remaining

        discount = subtotal - total

        return {
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "discount": discount.quantize(Decimal("0.01")),
            "total": total.quantize(Decimal("0.01")),
            "offers": applied_offers,
        }
