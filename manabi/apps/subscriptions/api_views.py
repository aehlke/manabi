import itunesiap
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from manabi.apps.subscriptions import products
from manabi.apps.subscriptions.models import Subscription
from manabi.apps.subscriptions.serializers import (
    PurchasingOptionsSerializer,
    PurchasedSubscriptionProduct,
)


@api_view(['GET'])
def purchasing_options(request):
    serializer = PurchasingOptionsSerializer(products.purchasing_options())
    return Response(serializer.data)


class SubscriptionViewSet(viewsets.ViewSet):
    serializer_class = PurchasingSubscriptionProduct
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = self.get_serializer(request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        try:
            Subscription.objects.process_itunes_receipt(
                request.user, serializer.data['itunes_receipt'])
        except itunesiap.exc.InvalidReceipt:
            raise ValidationError(
                "Invalid iTunes receipt; please contact support.")

        return Response(serializer.data)
