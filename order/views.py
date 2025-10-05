from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from payment.utils import create_cashier_payment

from product.models import Product
from .serializer import OrderSerializer, OrderItemsSerializer
from .models import Order, OrderItem, ShippingSetting
from .serializer import ShippingSettingSerializer

# Create your views here.


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders(request):
    orders = Order.objects.filter(user=request.user)
    serializer = OrderSerializer(orders, many=True)
    return Response({"order": serializer.data})


@api_view(["GET"])
def get_shipping(request):
    # جلب جميع الكائنات من موديل ShippingSetting
    shipping_settings = ShippingSetting.objects.all()

    # استخدام Serializer لتحويل الـ QuerySet إلى JSON
    serializer = ShippingSettingSerializer(shipping_settings, many=True)

    # إرجاع قائمة الـ JSON
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsAdminUser])
def process_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    order.order_status = request.data["status"]
    order.save()

    serializer = OrderSerializer(order, many=False)
    return Response({"order": serializer.data})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    order.delete()

    return Response({"details": "order deleted successfully"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    serializer = OrderSerializer(order, many=False)
    return Response({"order": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def new_order(request):
    user = request.user
    data = request.data
    order_items = data.get("order_items", [])

    if not order_items:
        return Response(
            {"error": "No Order Received"}, status=status.HTTP_400_BAD_REQUEST
        )

    total_amount = sum(item["price"] * item["quantity"] for item in order_items)

    # 1. Create Order
    order = Order.objects.create(
        user=user,
        customer_phone=data["customer_phone"],
        governorate=data["governorate"],
        city=data["city"],
        street=data["street"],
        total_amount=total_amount,
    )

    for i in order_items:
        product = Product.objects.get(id=i["product"])
        OrderItem.objects.create(
            product=product,
            order=order,
            name=product.name,
            quantity=i["quantity"],
            price=i["price"],
        )
        product.stock -= i["quantity"]
        product.save()

    # 2. Initialize Payment with OPay
    payment_url = create_cashier_payment(
        order_id=str(order.id),
        amount=str(int(total_amount * 100)),  # OPay بيستخدم الفلوس بالـ cents
        currency="EGP",
        return_url="https://your-frontend.com/payment/callback",  # غيّرها حسب الـ frontend بتاعك
    )

    if not payment_url:
        return Response(
            {"error": "Payment initialization failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Final response to frontend
    return Response(
        {
            "message": "Order created. Redirect to OPay to pay.",
            "payment_url": payment_url,
            "order_id": order.id,
        }
    )
