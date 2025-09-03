from django.db.models import F, Min, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
import django_filters
from .models import Product


class ProductsFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(method="filter_min_price")
    max_price = django_filters.NumberFilter(method="filter_max_price")
    brand = django_filters.BaseInFilter(field_name="brand", lookup_expr="in")
    category = django_filters.BaseInFilter(
        field_name="category__slug", lookup_expr="in"
    )

    class Meta:
        model = Product
        fields = ["brand", "category", "min_price", "max_price"]

    def filter_min_price(self, queryset, name, value):
        # نجيب أقل سعر variant في المنتج ونقارن انه >= value
        queryset = queryset.annotate(
            lowest_variant_price=Min(
                ExpressionWrapper(
                    F("variants__price") - Coalesce(F("variants__discount"), Value(0)),
                    output_field=DecimalField(),
                )
            )
        )
        return queryset.filter(lowest_variant_price__gte=value)

    def filter_max_price(self, queryset, name, value):
        # نفس الفكرة: أقل سعر variant في المنتج <= القيمة اللي المستخدم اختارها
        queryset = queryset.annotate(
            lowest_variant_price=Min(
                ExpressionWrapper(
                    F("variants__price") - Coalesce(F("variants__discount"), Value(0)),
                    output_field=DecimalField(),
                )
            )
        )
        return queryset.filter(lowest_variant_price__lte=value)
