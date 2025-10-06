from . import views
from django.urls import path

urlpatterns = [
    path("products/", views.get_all_products, name="products"),
    path("products/swiper/", views.get_swiper_products, name="products"),
    path("product/<slug:slug>/", views.get_by_id_product, name="get_by_id_product"),
    path("search/<str:keyword>/", views.search_products_view, name="search_products"),
    path("sales/", views.flash_sale_products, name="sales"),
    path("sales/swiper/", views.flash_sale_swiper, name="sales swiper"),
    path("categories/", views.get_all_categories, name="get_all_categories"),
    path("brands/", views.get_brands_by_filter, name="get_brands_by_filter"),
    path("offers/", views.get_offer_images, name="get_brands_by_filter"),
]
