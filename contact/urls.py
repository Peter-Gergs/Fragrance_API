from django.urls import path
from .views import contact_message_view

urlpatterns = [
    path("contact/", contact_message_view, name="contact-message"),
]
