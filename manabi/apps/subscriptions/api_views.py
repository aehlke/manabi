from rest_framework.decorators import api_view
from rest_framework.response import Response

from manabi.apps.subscriptions import products
from manabi.apps.subscriptions.serializers import (
    PurchasingOptionsSerializer,
)


@api_view(['GET'])
def purchasing_options(request):
    serializer = PurchasingOptionsSerializer(products.purchasing_options())
    return Response(serializer.data)
