from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import F, ExpressionWrapper, FloatField, Count
from django.db.models.functions import Cast
from rest_framework import status

from .models import Product, Category, OfferImage, ReviewsImage
from .serializers import ProductSerializer, OfferImageSerializer, ReviewsImageSerializer
from .filters import ProductsFilter
from .utils import search_products

pageSize = 24


@api_view(["GET"])
def get_all_products(request):
    products = ProductsFilter(
        request.GET, queryset=Product.objects.all().order_by("-priority", "-id")
    )
    paginator = PageNumberPagination()
    paginator.page_size = pageSize
    queryset = paginator.paginate_queryset(products.qs, request)
    serializer = ProductSerializer(queryset, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
def get_swiper_products(request):
    products = Product.objects.all().order_by("-priority", "-id")[:10]
    serializer = ProductSerializer(products, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
def get_by_id_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    serializer = ProductSerializer(product, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
def search_products_view(request, keyword):
    base_queryset = search_products(keyword)
    paginator = PageNumberPagination()
    paginator.page_size = pageSize

    # Apply filters by brand, category, min/max price
    brand = request.GET.get("brand")
    category = request.GET.get("category")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if brand:
        base_queryset = base_queryset.filter(brand__in=brand.split(","))
    if category:
        base_queryset = base_queryset.filter(category__name__in=category.split(","))
    if min_price:
        base_queryset = base_queryset.filter(price__gte=min_price)
    if max_price:
        base_queryset = base_queryset.filter(price__lte=max_price)

    # ✅ هنا التصحيح:
    result_page = paginator.paginate_queryset(base_queryset, request)
    serializer = ProductSerializer(result_page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


from .models import Product, Category, ProductVariant


@api_view(["GET"])
def flash_sale_products(request):
    # جلب الـ product ids اللي فيهم خصم
    discounted_variant_products_ids = (
        ProductVariant.objects.filter(
            discount__isnull=False,
            discount__gt=0,
            price__gt=0,
        )
        .annotate(
            discount_percentage=ExpressionWrapper(
                (Cast(F("discount"), FloatField()) / Cast(F("price"), FloatField()))
                * 100,
                output_field=FloatField(),
            )
        )
        .filter(discount_percentage__gte=5)
        .values_list("product_id", flat=True)
        .distinct()
    )

    # جلب المنتجات الفريدة بناءً على الـ ids
    discounted_products = Product.objects.filter(id__in=discounted_variant_products_ids)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    queryset = paginator.paginate_queryset(discounted_products, request)
    serializer = ProductSerializer(queryset, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
def flash_sale_swiper(request):
    discounted_products = (
        Product.objects.filter(
            variants__discount__isnull=False,
            variants__discount__gt=0,
            variants__price__gt=0,
        )
        .annotate(
            discount_percentage=ExpressionWrapper(
                (
                    Cast(F("variants__discount"), FloatField())
                    / Cast(F("variants__price"), FloatField())
                )
                * 100,
                output_field=FloatField(),
            )
        )
        .filter(discount_percentage__gte=5)
        .order_by("-discount_percentage")
        .distinct()[:5]
    )

    serializer = ProductSerializer(
        discounted_products, many=True, context={"request": request}
    )
    return Response(serializer.data)


@api_view(["GET"])
def get_normal_categories(request):
    categories = Category.objects.filter(is_special=False)
    data = []

    for cat in categories:
        data.append(
            {
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "short_description": cat.short_description,
                "is_special": cat.is_special,
                "special_title": cat.special_title,
                "special_description": cat.special_description,
                "image": (
                    request.build_absolute_uri(cat.image.url) if cat.image else None
                ),
            }
        )

    return Response(data)


@api_view(["GET"])
def get_special_categories(request):
    categories = Category.objects.filter(is_special=True)
    data = []

    for cat in categories:
        data.append(
            {
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "short_description": cat.short_description,
                "is_special": cat.is_special,
                "special_title": cat.special_title,
                "special_description": cat.special_description,
                "image": (
                    request.build_absolute_uri(cat.image.url) if cat.image else None
                ),
            }
        )

    return Response(data)


@api_view(["GET"])
def get_brands_by_filter(request):
    queryset = Product.objects.all()

    # Apply filters if exist
    category = request.GET.get("category")
    search = request.GET.get("search")

    if category:
        queryset = queryset.filter(category__name__iexact=category)

    if search:
        lang = request.headers.get("Accept-Language", "en")
        if lang == "ar":
            queryset = queryset.filter(name_ar__icontains=search)
        else:
            queryset = queryset.filter(name__icontains=search)

    # Count brands
    brand_counts = (
        queryset.values("brand").annotate(count=Count("brand")).order_by("-count")
    )
    top_brands = [item["brand"] for item in brand_counts[:10]]
    return Response(top_brands)


@api_view(["GET"])
def get_offer_images(request):
    queryset = OfferImage.objects.all().order_by("id")

    serializer = OfferImageSerializer(queryset, many=True, context={"request": request})

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_review_images(request):
    queryset = ReviewsImage.objects.all().order_by("id")

    serializer = ReviewsImageSerializer(
        queryset, many=True, context={"request": request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)
