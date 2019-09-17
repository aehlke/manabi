import logging

import itunesiap
from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from manabi.apps.subscriptions import products
from manabi.apps.subscriptions.models import (
    Subscription,
    PurchasedSubscriptionProduct,
    OutOfDateReceiptError,
    user_is_active_subscriber,
)
from manabi.apps.subscriptions.serializers import (
    PurchasingOptionsSerializer,
    PurchasedSubscriptionProductSerializer,
    SubscriptionStatusSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
def purchasing_options(request):
    serializer = PurchasingOptionsSerializer(products.purchasing_options())
    return Response(serializer.data)


@api_view(['GET'])
def manabi_reader_purchasing_options(request):
    serializer = PurchasingOptionsSerializer(
        products.manabi_reader_purchasing_options())
    return Response(serializer.data)


@api_view(['GET'])
def subscription_status(request):
    serializer = SubscriptionStatusSerializer(
        {'active': user_is_active_subscriber(request.user)})
    return Response(serializer.data)


class SubscriptionViewSet(viewsets.GenericViewSet):
    serializer_class = PurchasedSubscriptionProductSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        try:
            itunes_receipt = request.data['itunes_receipt']
        except KeyError:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        try:
            Subscription.objects.process_itunes_receipt(
                request.user, itunes_receipt)
        except itunesiap.exc.InvalidReceipt:
            logger.error('InvalidReceipt', exc_info=True)

            raise ValidationError(
                "Invalid iTunes receipt; please contact support.")
        except OutOfDateReceiptError:
            raise ValidationError(
                "iTunes purchase receipt is out of date. Please "
                "restore purchases.")

        purchased_subscription_product = PurchasedSubscriptionProduct(
            request.user, itunes_receipt)
        serializer = self.get_serializer(purchased_subscription_product)

        return Response(serializer.data)


@api_view(['POST'])
def subscription_update_notification(request):
    logger.info('Received subscription update notification')

    try:
        Subscription.objects.process_itunes_subscription_update_notification(
            request.data)
    except itunesiap.exc.InvalidReceipt:
        logger.error('InvalidReceipt', exc_info=True)

        raise ValidationError(
            "Invalid iTunes receipt; please contact support.")

    return HttpResponse('')
