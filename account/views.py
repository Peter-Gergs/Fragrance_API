from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework import status

from django.conf import settings
from .serializers import SignUpSerialzer, UserSerialzer
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
import secrets
from django.core.mail import send_mail

# Create your views here.


@api_view(["POST"])
def register(request):
    serializer = SignUpSerialzer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        if not User.objects.filter(username=data["email"]).exists():
            user = User.objects.create(
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                username=data["email"],
                password=make_password(data["password"]),
            )
            return Response(
                {"details": "Account Created Successfully"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"error": "This Email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = UserSerialzer(request.user, many=False)
    return Response(user.data)


def get_current_host(request):
    protocol = request.is_secure() and "https" or "http"
    host = request.get_host()
    return "{protocol}://{host}/".format(protocol=protocol, host=host)


@api_view(["POST"])
def forgot_password(request):
    data = request.data
    email = data.get("email")
    if not email:
        return Response({"error": "This Email not Exist"}, status=400)
    user = get_object_or_404(User, email=email)
    token = str(secrets.randbelow(900000) + 100000)
    expire_date = datetime.now() + timedelta(minutes=10)
    user.profile.reset_password_token = token
    user.profile.reset_password_expire = expire_date
    user.profile.save()

    host = get_current_host(request)
    body = "Your password Reset Code Is: {token}".format(token=token)
    send_mail(
        "Password reset for Future",
        body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
    return Response({"details": "Password reset sent to {email}".format(email=email)})


@api_view(["GET"])
def verify_reset_token(request, token):
    user = get_object_or_404(User, profile__reset_password_token=token)
    if user.profile.reset_password_expire.replace(tzinfo=None) < datetime.now():
        return Response({"error": "Token is expired"}, status=400)

    return Response({"message": "Token is valid", "username": user.username})


@api_view(["POST"])
def reset_password(request, token):
    user = get_object_or_404(User, profile__reset_password_token=token)

    if user.profile.reset_password_expire.replace(tzinfo=None) < datetime.now():
        return Response({"error": "Token is expired"}, status=400)

    password = request.data.get("password")
    confirm_password = request.data.get("confirm_password")

    if password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)

    user.password = make_password(password)
    user.profile.reset_password_token = ""
    user.profile.reset_password_expire = None
    user.save()
    user.profile.save()

    return Response({"message": "Password has been reset successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    data = request.data
    if not user.check_password(data["current_password"]):
        return Response({"error": "Wrong current password"}, status=400)
    if data["new_password"] != data["confirm_password"]:
        return Response({"error": "Passwords do not match"}, status=400)
    user.set_password(data["new_password"])
    user.save()
    return Response({"message": "Password updated successfully"})
