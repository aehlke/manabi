import logging

import itunesiap
from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied
from raven.contrib.django.raven_compat.models import client as raven_client
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

logger = logging.getLogger(__name__)


@api_view(['GET'])
def purchasing_options(request):
    serializer = PurchasingOptionsSerializer(products.purchasing_options())
    return Response(serializer.data)


class SubscriptionViewSet(viewsets.GenericViewSet):
    serializer_class = PurchasedSubscriptionProduct
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        try:
            Subscription.objects.process_itunes_receipt(
                request.user, serializer.data['itunes_receipt'])
        except itunesiap.exc.InvalidReceipt:
            raven_client.captureException()

            raise ValidationError(
                "Invalid iTunes receipt; please contact support.")

        return Response(serializer.data)


@api_view(['POST'])
def subscription_update_notification(request):
    logger.info('Received subscription update notification')

    try:
        Subscription.objects.process_itunes_subscription_update_notification(
            request.data)
    except itunesiap.exc.InvalidReceipt:
        raven_client.captureException()

        raise ValidationError(
            "Invalid iTunes receipt; please contact support.")

    return HttpResponse('')
