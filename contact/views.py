from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializers import ContactMessageSerializer
from rest_framework.permissions import IsAuthenticated


# Create your views here.


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def contact_message_view(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Message sent successfully!"}, status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
