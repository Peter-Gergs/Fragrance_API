from django.urls import path
from .views import get_offers, featured_offers

urlpatterns = [
    path("", get_offers),
    path("featured/", featured_offers, name="featured-offers"),
]
