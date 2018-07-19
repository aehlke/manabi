from datetime import datetime
import logging

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.db import models
import itunesiap

logger = logging.getLogger(__name__)


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
            subscriber=user,
            defaults={
                'expires_date': expires_date,
            },
        )
        if not created and (
            not subscription.active or subscription.expires_date < expires_date
        ):
            subscription.active = True
            subscription.expires_date = expires_date
            subscription.save()

    def process_itunes_receipt(
        self, user, itunes_receipt, log_purchase=True,
    ):
        '''
        Subscribes if valid.

        Will raise InvalidReceipt error if invalid.
        '''
        if log_purchase:
            InAppPurchaseLogItem.objects.create(
                subscriber=user,
                itunes_receipt=itunes_receipt,
            )

        response = itunesiap.verify(
            itunes_receipt,
            password=settings.ITUNES_SHARED_SECRET,
            env=itunesiap.env.review)
        latest_receipt_info = response.latest_receipt_info[-1]
        self.model.objects.subscribe(
            user,
            _receipt_date_to_datetime(latest_receipt_info['expires_date_ms']))

        logger.info('Processed iTunes receipt')

    def process_itunes_subscription_update_notification(self, notification):
        '''
        Will raise InvalidReceipt error if invalid.
        '''
        shared_secret = notification['password']
        if shared_secret != settings.ITUNES_SHARED_SECRET:
            raise PermissionDenied('Invalid iTunes shared secret.')

        SubscriptionUpdateNotificationLogItem.objects.create(
            receipt_info=notification['latest_receipt_info'])

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

            response = itunesiap.verify(
                receipt, password=settings.ITUNES_SHARED_SECRET)
            latest_receipt_info = response.latest_receipt_info[-1]
            original_transaction_id = (
                latest_receipt_info['original_transaction_id'])

            subscription, created = Subscription.objects.get_or_create(
                original_transaction_id=original_transaction_id)
            subscription.active = True
        elif notification_type == 'CANCEL':
            receipt = itunes_receipt['latest_expired_receipt']
            receipt_info = notification['latest_expired_receipt_info']

            response = itunesiap.verify(
                receipt, password=settings.ITUNES_SHARED_SECRET)
            latest_receipt_info = response.latest_receipt_info[-1]
            original_transaction_id = (
                latest_receipt_info['original_transaction_id'])

            subscription = Subscription.objects.get(
                original_transaction_id=original_transaction_id)
            subscription.active = False
        elif notification_type == 'DID_CHANGE_RENEWAL_PREF':
            # Customer changed the plan that takes affect at the next
            # subscription renewal. Current active plan is not affected.
            return

        subscription.sandbox = environment == itunesiap.env.sandbox
        subscription.latest_itunes_receipt = receipt
        subscription.expires_date = _receipt_date_to_datetime(
            receipt_info['expires_date_ms'])
        subscription.save()

        logger.info('Processed iTunes subscription update notification')


class Subscription(models.Model):
    objects = SubscriptionManager()

    subscriber = models.ForeignKey(
        User, models.CASCADE, unique=True, db_index=True, editable=False)

    expires_date = models.DateTimeField()
    active = models.BooleanField(default=True, blank=True)
    sandbox = models.BooleanField(default=False, blank=True)

    original_transaction_id = models.CharField(max_length=300)
    latest_itunes_receipt = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)


class InAppPurchaseLogItem(models.Model):
    itunes_receipt = models.TextField(editable=False)
    subscriber = models.ForeignKey(User, models.CASCADE, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def process_itunes_receipt(self):
        '''
        Useful for replaying a transaction that failed due to a bug.
        '''
        Subscription.objects.process_itunes_receipt(
            self.subscriber, self.itunes_receipt, log_purchase=False)


class SubscriptionUpdateNotificationLogItem(models.Model):
    receipt_info = JSONField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
