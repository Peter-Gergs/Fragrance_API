from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from django.conf import settings
from .models import Cart, CartItem
from order.models import (
    Order,
    OrderItem,
    ShippingSetting,
    PaymentStatus,
)  # <=== أضفنا PaymentStatus هنا
from .serializers import CartSerializer
from product.models import ProductVariant
from payment.utils import create_cashier_payment
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
import sys
from payment.models import PaymentTransaction  # <=== تم الإضافة
import json  # تم الإضافة
import secrets
from django.db import transaction as db_transaction
from django.db.models import F
import logging
from offers.services import OfferService


def get_or_create_cart(request):
    """ترجع الكارت سواء لليوزر أو للضيف"""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


@api_view(["GET"])
def get_cart(request):
    cart = get_or_create_cart(request)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(["POST"])
def add_to_cart(request):
    variant_id = request.data.get("variant_id")
    quantity = int(request.data.get("quantity", 1))

    variant = get_object_or_404(ProductVariant, id=variant_id)

    if quantity > variant.stock:
        return Response(
            {"error": "Requested quantity exceeds available stock."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cart = get_or_create_cart(request)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)

    total_quantity = quantity if created else cart_item.quantity + quantity

    if total_quantity > variant.stock:
        return Response(
            {"error": "Total quantity in cart exceeds available stock."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cart_item.quantity = total_quantity
    cart_item.save()

    return Response(
        {"message": "Variant added to cart successfully."},
        status=status.HTTP_200_OK,
    )


@api_view(["PATCH"])
def update_cart_item_quantity(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    quantity = int(request.data.get("quantity", 1))
    if quantity < 1:
        return Response({"error": "Quantity must be at least 1."}, status=400)
    if quantity > item.variant.stock:
        return Response(
            {"error": "Requested quantity exceeds available stock."}, status=400
        )

    item.quantity = quantity
    item.save()
    return Response({"message": "Quantity updated.", "quantity": item.quantity})


@api_view(["DELETE"])
def delete_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return Response({"message": "Item deleted from cart."})


@api_view(["POST"])
def buy_now(request):
    """
    BuyNow: clear current cart (user or guest), add a product, prepare for checkout.
    """
    print("🛒 BuyNow called:", request.data, file=sys.stderr)

    variant_id = request.data.get("variant_id")
    quantity = int(request.data.get("quantity", 1))

    if not variant_id:
        return Response({"error": "variant_id is required."}, status=400)

    # 🟢 استخدم نفس الفانكشن الذكية اللي عندك
    cart = get_or_create_cart(request)

    # 🧹 نحذف محتويات الكارت القديمة
    cart.items.all().delete()

    # 🛍 نضيف المنتج الجديد
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if quantity > variant.stock:
        return Response(
            {"error": "Requested quantity exceeds available stock."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    CartItem.objects.create(cart=cart, variant=variant, quantity=quantity)

    # ✅ نرجع استجابة بسيطة — المستخدم هيتحول بعدها لصفحة Checkout
    return Response(
        {
            "message": "Product added successfully for checkout.",
            "variant": variant.id,
            "quantity": quantity,
            "cart_id": cart.id,
            "is_guest": not request.user.is_authenticated,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def initiate_payment(request):
    print("🔔 Data received from Checkout Form:", request.data, file=sys.stderr)
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()

    if not cart_items.exists():
        return Response({"error": "Cart is empty."}, status=400)

    offer_result = OfferService().calculate(cart)
    subtotal = offer_result["total"]
    receipt_token = secrets.token_hex(32)

    shipping_setting = (
        ShippingSetting.objects.filter(
            governorate=request.data.get("governorate")
        ).first()
        or ShippingSetting.objects.first()
    )
    shipping_cost = shipping_setting.cost if shipping_setting else 65
    total_amount = 0

    if request.data.get("method") == "cash":
        # Cash on delivery: only a deposit is charged online
        total_amount = 200 if subtotal + shipping_cost >= 1500 else 100
    else:
        total_amount = subtotal + shipping_cost

    amount = int((Decimal(total_amount) * 100).to_integral_value())

    # 2. بيانات العميل
    if request.user.is_authenticated:
        user_info = {
            "userId": str(request.user.id),
            "phone": request.data.get("customer_phone"),
            "email": request.user.email or "test@example.com",
            "name": request.user.get_full_name() or "Guest",
        }
    else:
        # لو ضيف — ناخد بياناته من الريكوست
        user_info = {
            "userId": "guest",
            "phone": request.data.get("customer_phone"),
            "email": request.data.get("customer_email"),
            "name": request.data.get("customer_name", "Guest"),
        }

    # 3. المنتجات
    total_quantity = sum(item.quantity for item in cart_items)

    product_list = [
        {
            "productId": "cart_summary",
            "name": f"Order Summary ({total_quantity} items)",
            "description": "Multiple product variants from your cart",
            "quantity": 1,
            "price": str(int(subtotal * 100)),  # نحول للمليمات (piasters)
        }
    ]

    result = create_cashier_payment(
        amount=amount,
        currency="EGP",
        return_url=f"{settings.FRONTEND_URL}/payment/return/",
        cancel_url=f"{settings.FRONTEND_URL}/payment/cancel/",
        callback_url=f"{settings.BACKEND_URL}/api/payment/callback/",
        user_info=user_info,
        product_list=product_list,
    )

    opay_reference = result.get("reference")

    # === 4. التحقق من الـ reference ===
    if not opay_reference:
        error_message = result.get(
            "error", "Payment processing failed. Please try again."
        )
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
    # ===============================================

    checkout_data = {
        "customer_phone": request.data.get("customer_phone"),
        "governorate": request.data.get("governorate"),
        "city": request.data.get("city"),
        "street": request.data.get("street"),
        "building_number": request.data.get("building_number"),
        "floor_number": request.data.get("floor_number"),
        "apartment_number": request.data.get("apartment_number"),
        "landmark": request.data.get("landmark"),
        "name": request.data.get("name"),
        "method": request.data.get("method"),
        "shipping_cost": str(shipping_cost),
    }

    if not checkout_data.get("customer_phone"):
        return Response(
            {"error": "Customer phone is required for checkout."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Snapshot ensures the charged price and receipt cannot drift while paying.
    snapshot = {
        "items": [{"variant_id": item.variant_id, "name": item.variant.product.name,
                   "quantity": item.quantity, "unit_price": str(Decimal(item.variant.price) - Decimal(item.variant.discount or 0))}
                  for item in cart_items.select_related("variant__product")],
        "subtotal": str(offer_result["subtotal"]),
        "discount": str(offer_result["discount"]),
        "offers": offer_result["offers"],
        "shipping": str(shipping_cost),
        "total": str(offer_result["total"] + shipping_cost),
        "amount_paid": str(total_amount),
    }
    # إنشاء سجل المعاملة الدائم
    PaymentTransaction.objects.create(
        checkout_snapshot=snapshot, receipt_token=receipt_token,
        opay_reference=opay_reference,
        cart=cart,
        checkout_address_json=checkout_data,
        status="PENDING",
    )

    # نرجع فقط بيانات النجاح
    return Response(
        {
            "reference": result.get("reference"),
            "redirect_url": result.get("redirect_url"),
            "receipt_token": receipt_token,
        }
    )


# ----------------------------------------------------------------------------------------------------------------------


@csrf_exempt
@api_view(["POST"])
def opay_webhook(request):
    # IMPORTANT: Authenticate OPay callback signatures / verify payment server-to-server
    # using your merchant integration BEFORE trusting payload.status.
    payload = request.data.get("payload") or {}
    reference, payment_status = payload.get("reference"), payload.get("status")
    if not reference:
        return Response({"error": "Missing reference"}, status=400)
    # Never trust an unsigned success notification. Configure OPAY_WEBHOOK_SECRET
    # and validate the actual signature scheme documented for your OPay account.
    from django.conf import settings
    if not getattr(settings, "OPAY_WEBHOOK_VERIFIER", None):
        return Response({"error": "Payment verification not configured"}, status=503)
    if not settings.OPAY_WEBHOOK_VERIFIER(request):
        return Response({"error": "Invalid payment signature"}, status=403)
    with db_transaction.atomic():
        txn = PaymentTransaction.objects.select_for_update().filter(opay_reference=reference).first()
        if not txn:
            existing = Order.objects.filter(opay_reference=reference).first()
            return Response({"status": "Already processed"} if existing else {"error": "Unknown reference"}, status=200 if existing else 404)
        if payment_status != "SUCCESS":
            txn.status = payment_status or "UNKNOWN"
            txn.save(update_fields=["status"])
            return Response({"status": "Payment not confirmed"})
        snapshot = txn.checkout_snapshot
        if not snapshot or not snapshot.get("items"):
            return Response({"error": "Missing checkout snapshot"}, status=409)
        checkout = txn.checkout_address_json
        cart = txn.cart
        order = Order.objects.create(
            user=cart.user if cart else None, username=checkout.get("name"),
            customer_phone=checkout.get("customer_phone") or "",
            governorate=checkout.get("governorate") or "", city=checkout.get("city") or "",
            street=checkout.get("street") or "", building_number=checkout.get("building_number"),
            floor_number=checkout.get("floor_number"), apartment_number=checkout.get("apartment_number"),
            landmark=checkout.get("landmark"), opay_reference=reference,
            total_amount=Decimal(snapshot["total"]), shipping_cost=Decimal(snapshot["shipping"]),
            discount_amount=Decimal(snapshot["discount"]), applied_offers=snapshot["offers"],
            amount_paid=Decimal(snapshot["amount_paid"]),
            payment_method=checkout.get("method", "visa"), receipt_token=txn.receipt_token,
            payment_status=PaymentStatus.SHIPPING_PAID if checkout.get("method") == "cash" else PaymentStatus.PAID,
        )
        for item in snapshot["items"]:
            variant = ProductVariant.objects.select_for_update().select_related("product").get(pk=item["variant_id"])
            if variant.stock < item["quantity"]:
                # Payment was collected: retain transaction for manual fulfillment/refund.
                raise ValueError("Insufficient stock after payment; manual reconciliation required")
            OrderItem.objects.create(
                order=order, product=variant.product, variant=variant,
                name=item["name"], quantity=item["quantity"], price=Decimal(item["unit_price"]),
            )
            variant.stock = F("stock") - item["quantity"]
            variant.save(update_fields=["stock"])
        if cart:
            # Only remove items that still match the checkout snapshot.
            for item in snapshot["items"]:
                cart_item = cart.items.filter(variant_id=item["variant_id"]).first()
                if cart_item and cart_item.quantity == item["quantity"]:
                    cart_item.delete()
        txn.delete()
    return Response({"status": "Order created successfully", "order_id": order.pk})


@api_view(["GET"])
def get_order_by_reference(request):
    reference = request.query_params.get("reference")

    if not reference:
        return Response({"error": "Reference is required"}, status=400)

    # 1. لو لسه الأوردر متعملش — transaction لسه موجود
    try:
        transaction = PaymentTransaction.objects.get(opay_reference=reference)
        return Response({"status": transaction.status, "order_id": None})
    except PaymentTransaction.DoesNotExist:
        pass

    # 2. لو الأوردر اتعمل
    order = Order.objects.filter(opay_reference=reference).first()
    if order:
        return Response(
            {
                "status": "SUCCESS",
                "order_id": order.id,
            }
        )

    return Response({"error": "Reference not found"}, status=404)
