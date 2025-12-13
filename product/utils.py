from django.db.models import Q, Value, IntegerField, Case, When
from .models import Product


def search_products(query):
    query = query.strip().lower()

    return (
        Product.objects.annotate(
            search_priority=Case(
                When(Q(name__icontains=query), then=Value(1)),
                When(Q(description__icontains=query), then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        )
        .filter(Q(name__icontains=query) | Q(description__icontains=query))
        .order_by("search_priority")
    )
