from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("cart/", views.get_cart, name="get_cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path(
        "cart/item/<int:item_id>/delete/",
        views.delete_cart_item,
        name="delete_cart_item",
    ),
    path(
        "cart/item/<int:item_id>/update/",
        views.update_cart_item_quantity,
        name="update_cart_quantity",
    ),
    # Pending Order Flow
    # Payment Flow
    path("payment/pay/", views.initiate_payment, name="initiate_payment"),
    path("payment/webhook/", csrf_exempt(views.opay_webhook), name="payment_webhook"),
    path("payment/callback/", csrf_exempt(views.opay_webhook), name="payment_callback"),
]


from django.views.generic.base import RedirectView
