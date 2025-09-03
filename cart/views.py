from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from django.conf import settings
from .models import Cart, CartItem
from order.models import Order, OrderItem, ShippingSetting
from .serializers import CartSerializer
from product.models import ProductVariant
from payment.utils import create_cashier_payment


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    variant_id = request.data.get("variant_id")
    quantity = int(request.data.get("quantity", 1))

    variant = get_object_or_404(ProductVariant, id=variant_id)

    if quantity > variant.stock:
        return Response(
            {"error": "Requested quantity exceeds available stock."}, status=400
        )

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)

    total_quantity = quantity if created else cart_item.quantity + quantity
    if total_quantity > variant.stock:
        return Response({"error": "Total quantity in cart exceeds stock."}, status=400)

    cart_item.quantity = total_quantity
    cart_item.save()
    return Response({"message": "Variant added to cart successfully."})


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_cart_item_quantity(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
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
@permission_classes([IsAuthenticated])
def delete_cart_item(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return Response({"message": "Item deleted from cart."})


@api_view(["POST"])
def initiate_payment(request):
    user = request.user

    # 1. اجمع بيانات الكارت
    cart = Cart.objects.get(user=user)
    cart_items = cart.items.all()

    subtotal = sum(
        (item.variant.price - (item.variant.discount or 0)) * item.quantity
        for item in cart_items
    )
    shipping_cost = ShippingSetting.objects.first().cost
    total_amount = subtotal + (shipping_cost)
    amount = int(total_amount * 100)
    print(amount)
    # 2. جهز بيانات العميل
    user_info = {
        "userId": str(user.id),
        "phone": request.data.get("customer_phone"),
        "email": user.email or "test@example.com",
        "name": user.get_full_name() or "Guest",
    }

    # 3. جهز قائمة المنتجات
    product_list = []
    for item in cart_items:
        product_list.append(
            {
                "productId": item.id,
                "name": item.variant.product.name,
                "description": item.variant.product.description or "No description",
                "quantity": item.quantity,
                "price": str(int(item.variant.price * 100)),
            }
        )
    print(product_list)
    # 4. استدعاء util
    result = create_cashier_payment(
        amount=amount,
        currency="EGP",
        return_url=f"{settings.FRONTEND_URL}/payment/return",
        cancel_url=f"{settings.FRONTEND_URL}/payment/cancel",
        callback_url=f"{settings.BACKEND_URL}/api/payment/callback",
        user_info=user_info,
        product_list=product_list,
    )

    return Response(result)


@api_view(["POST"])
def opay_webhook(request):
    """
    بعد نجاح الدفع، ينشئ Order وينقل كل CartItem إلى OrderItem
    """
    data = request.data
    if data.get("status") != "SUCCESS":
        return Response({"status": "Ignored (not successful)"})

    reference = data.get("reference")
    # يمكن البحث عن Cart عبر reference إذا خزناه، هنا نفترض استخدام session
    from django.contrib.sessions.models import Session

    sessions = Session.objects.all()
    cart = None
    for session in sessions:
        s_data = session.get_decoded()
        if s_data.get("opay_reference") == reference:
            user_id = s_data.get("_auth_user_id")
            from django.contrib.auth import get_user_model

            user = get_user_model().objects.get(id=user_id)
            cart = Cart.objects.get(user=user)
            checkout_address = s_data.get("checkout_address")
            break

    if not cart:
        return Response({"error": "Cart not found for this payment."}, status=404)

    # إنشاء Order
    order = Order.objects.create(
        user=cart.user,
        customer_phone=checkout_address.get("customer_phone"),
        governorate=checkout_address.get("governorate"),
        city=checkout_address.get("city"),
        street=checkout_address.get("street"),
        building_number=checkout_address.get("building_number"),
        floor_number=checkout_address.get("floor_number"),
        apartment_number=checkout_address.get("apartment_number"),
        landmark=checkout_address.get("landmark"),
        total_amount=0,
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
        )
        item.variant.stock -= item.quantity
        products_to_update.append(item.variant)

    order.total_amount = total_amount
    order.save()
    cart.items.all().delete()
    # تحديث المخزون
    for variant in products_to_update:
        variant.save()

    return Response({"status": "Order created successfully"})
