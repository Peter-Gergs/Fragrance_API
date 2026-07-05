from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Offer
from .serializers import OfferSerializer


@api_view(["GET"])
def get_offers(request):

    offers = Offer.objects.filter(active=True).order_by(
        "priority", "size_ml", "required_quantity"
    )

    serializer = OfferSerializer(
        offers,
        many=True,
        context={"request": request},
    )

    return Response(serializer.data)


@api_view(["GET"])
def featured_offers(request):
    offers = Offer.objects.filter(active=True).order_by(
        "priority", "size_ml", "required_quantity"
    )[:4]

    serializer = OfferSerializer(offers, many=True, context={"request": request})

    return Response(serializer.data)
