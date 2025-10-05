from django.urls import path
from . import views

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
    path("payment/webhook/", views.opay_webhook, name="payment_webhook"),
    path("payment/callback/", views.opay_webhook, name="payment_callback"),
]


from django.views.generic.base import RedirectView

urlpatterns += [
    path("payment/webhook", RedirectView.as_view(url="/api/payment/webhook/", permanent=True)),
    path("payment/callback", RedirectView.as_view(url="/api/payment/callback/", permanent=True)),
]