from . import views
from django.urls import path

urlpatterns = [
    path("register/", views.register, name="register"),
    path("userinfo/", views.current_user, name="user_info"),
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path("password/verify/<str:token>/", views.verify_reset_token),
    path("password/reset/<str:token>/", views.reset_password),
    path("change_password/", views.change_password, name="change_password"),
]
