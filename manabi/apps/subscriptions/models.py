from datetime import datetime

from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
import itunesiap


def _receipt_date_to_datetime(receipt_date):
    return datetime.fromtimestamp(int(receipt_date) / 1000.0)


def user_is_active_subscriber(user):
    try:
        subscription = Subscription.objects.get(
            subscriber=user,
            active=True,
        )
        return subscription.expires_date >= datetime.utcnow()
    except Subscription.DoesNotExist:
        return False


class SubscriptionManager(models.Manager):
    def subscribe(self, user, expires_date):
        subscription, created = Subscription.objects.get_or_create(
            subscriber=request.user,
        )
        if not created and not subscription.active:
            subscription.active = True
            subscription.expires_date = expires_date
            subscription.save()

    def process_itunes_receipt(self, user, itunes_receipt):
        '''
        Subscribes if valid.

        Will raise InvalidReceipt error if invalid.
        '''
        response = itunesiap.verify(
            itunes_receipt,
            password=settings.ITUNES_SHARED_SECRET,
            env=itunesiap.env.review)
        latest_receipt_info = response.latest_receipt_info[-1]
        self.model.objects.subscribe(
            user, _receipt_date_to_datetime(latest_receipt_info['expire_date']))

    def process_itunes_subscription_update_notification(
        self, user, notification,
    ):
        '''
        Will raise InvalidReceipt error if invalid.
        '''
        shared_secret = notification['password']
        if shared_secret != settings.ITUNES_SHARED_SECRET:
            raise PermissionDenied('Invalid iTunes shared secret.')

        if notification['environment'] == 'PROD':
            environment = itunesiap.env.production
        else:
            environment = itunesiap.env.sandbox

        notification_type = notification['notification_type']

        if notification_type in [
            'INITIAL_BUY', 'RENEWAL', 'INTERACTIVE_RENEWAL',
        ]:
            receipt = notification['latest_receipt']
            receipt_info = notification['latest_receipt_info']

            itunesiap.verify(receipt, password=settings.ITUNES_SHARED_SECRET)

            subscription, created = Subscription.objects.get_or_create(
                subscriber=user)
            subscription.active = True
        elif notification_type == 'CANCEL':
            receipt = itunes_receipt['latest_expired_receipt']
            receipt_info = notification['latest_expired_receipt_info']

            itunesiap.verify(receipt, password=settings.ITUNES_SHARED_SECRET)

            subscription = Subscription.objects.get(subscriber=user)
            subscription.active = False

        subscription.sandbox = environment == itunesiap.env.sandbox
        subscription.latest_itunes_receipt = receipt
        subscription.expires_date = _receipt_date_to_datetime(
            receipt_info['expires_date'])
        subscription.save()


class Subscription(models.Model):
    objects = SubscriptionManager()

    subscriber = models.ForeignKey(
        User, unique=True, db_index=True, editable=False)

    expires_date = models.DateTimeField()
    active = models.BooleanField(default=True, blank=True)
    sandbox = models.BooleanField(default=False, blank=True)

    latest_itunes_receipt = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
