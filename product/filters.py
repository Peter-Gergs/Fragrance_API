from django.db.models import F, Min, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
import django_filters

from .models import Product


class ProductsFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(method="filter_min_price")
    max_price = django_filters.NumberFilter(method="filter_max_price")

    brand = django_filters.BaseInFilter(
        field_name="brand",
        lookup_expr="in"
    )

    category = django_filters.CharFilter(
        method="filter_category"
    )

    class Meta:
        model = Product
        fields = [
            "brand",
            "category",
            "min_price",
            "max_price",
        ]

    def filter_category(self, queryset, name, value):
        categories = [
            category.strip()
            for category in value.split(",")
            if category.strip()
        ]

        # Men category should also include Unisex products
        if "men" in categories and "unisex" not in categories:
            categories.append("unisex")

        # Women category should also include Unisex products
        if "women" in categories and "unisex" not in categories:
            categories.append("unisex")

        return queryset.filter(
            category__slug__in=categories
        ).distinct()

    def filter_min_price(self, queryset, name, value):
        queryset = queryset.annotate(
            lowest_variant_price=Min(
                ExpressionWrapper(
                    F("variants__price")
                    - Coalesce(
                        F("variants__discount"),
                        Value(0)
                    ),
                    output_field=DecimalField(),
                )
            )
        )

        return queryset.filter(
            lowest_variant_price__gte=value
        )

    def filter_max_price(self, queryset, name, value):
        queryset = queryset.annotate(
            lowest_variant_price=Min(
                ExpressionWrapper(
                    F("variants__price")
                    - Coalesce(
                        F("variants__discount"),
                        Value(0)
                    ),
                    output_field=DecimalField(),
                )
            )
        )

        return queryset.filter(
            lowest_variant_price__lte=value
        )
