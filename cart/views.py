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

    subtotal = OfferService().calculate(cart)

    shipping_setting = (
        ShippingSetting.objects.filter(
            governorate=request.data.get("governorate")
        ).first()
        or ShippingSetting.objects.first()
    )
    shipping_cost = shipping_setting.cost if shipping_setting else 65
    total_amount = (
        (100) if (request.data.get("method") == "cash") else (subtotal + shipping_cost)
    )
    amount = int(total_amount * 100)

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

    # إنشاء سجل المعاملة الدائم
    PaymentTransaction.objects.create(
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
        }
    )


# ----------------------------------------------------------------------------------------------------------------------


@csrf_exempt
@api_view(["POST"])
def opay_webhook(request):
    """
    Production-ready OPay webhook handler using PaymentTransaction model
    """
    print("🔔 OPay Webhook Received:", request.data, file=sys.stderr)

    # الحصول على payload
    payload = request.data.get("payload", {})
    if not payload:
        print("⚠️ Missing payload in webhook", file=sys.stderr)
        return Response({"error": "Missing payload"}, status=400)
    reference = payload.get("reference")
    status = payload.get("status")
    if not reference:
        print("⚠️ Missing reference in webhook", file=sys.stderr)
        return Response({"error": "Missing reference"}, status=400)

    try:
        transaction = PaymentTransaction.objects.get(opay_reference=reference)
    except PaymentTransaction.DoesNotExist:
        print(
            f"❌ PaymentTransaction not found for reference {reference}",
            file=sys.stderr,
        )
        return Response({"error": "Payment reference not found."}, status=404)

    if transaction.status == "SUCCESS":
        print(f"ℹ️ Transaction already processed: {reference}", file=sys.stderr)
        return Response({"status": "Already processed"})

    transaction.status = status
    transaction.save()

    if status != "SUCCESS":
        print(
            f"ℹ️ Payment not successful, status={status}, reference={reference}",
            file=sys.stderr,
        )
        return Response({"status": f"Ignored (status={status})"})

    # 2. استخراج البيانات من الـ Transaction <=== التعديل هنا
    cart = transaction.cart
    checkout_address = transaction.checkout_address_json

    if not cart:
        # لو الكارت اتحذف لسبب ما قبل Webhook
        print(
            f"❌ Cart not found in transaction for reference {reference}",
            file=sys.stderr,
        )
        return Response({"error": "Associated cart not found."}, status=404)

    user = cart.user  # لو كان المستخدم مسجل دخوله

    # إنشاء الأوردر
    order = Order.objects.create(
        user=user,
        username=checkout_address.get("name"),
        customer_phone=checkout_address.get("customer_phone"),
        governorate=checkout_address.get("governorate"),
        city=checkout_address.get("city"),
        street=checkout_address.get("street"),
        building_number=checkout_address.get("building_number"),
        floor_number=checkout_address.get("floor_number"),
        apartment_number=checkout_address.get("apartment_number"),
        landmark=checkout_address.get("landmark"),
        total_amount=Decimal("0.0"),
        payment_status=(
            PaymentStatus.SHIPPING_PAID
            if checkout_address.get("method") == "cash"
            else PaymentStatus.PAID
        ),
        opay_reference=reference,
    )
    total_amount = Decimal("0.0")
    products_to_update = []
    for item in cart.items.select_related("variant").all():
        price = Decimal(item.variant.price) - Decimal(item.variant.discount or 0)
        total_amount += price * item.quantity
        OrderItem.objects.create(
            order=order,
            product=item.variant.product,
            name=item.variant.product.name,
            quantity=item.quantity,
            price=price,
            variant=item.variant,
        )
        item.variant.stock -= item.quantity
        products_to_update.append(item.variant)

    # تحديث الإجمالي والمخزون
    shipping_cost = Decimal(checkout_address.get("shipping_cost", "0.0"))
    order.shipping_cost = shipping_cost
    order.total_amount = total_amount + shipping_cost
    order.save()

    # حذف محتويات الكارت فقط، وليس الكارت نفسه
    cart.items.all().delete()

    for variant in products_to_update:
        variant.save()

    # 4. حذف سجل المعاملة بعد نجاح إنشاء الأوردر
    transaction.delete()

    print(
        f"✅ Order created successfully for reference {reference}, order_id={order.id}",
        file=sys.stderr,
    )

    return Response({"status": "Order created successfully", "order_id": order.id})


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
