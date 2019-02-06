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
    def subscribe(
        self, user, original_transaction_id, expires_date,
        is_trial_period=False,
    ):
        subscription, created = Subscription.objects.get_or_create(
            subscriber=user,
            defaults={
                'expires_date': expires_date,
                'original_transaction_id': original_transaction_id,
            },
        )
        if not created and (
            not subscription.active or subscription.expires_date < expires_date
        ):
            subscription.active = True
            subscription.expires_date = expires_date
            subscription.is_trial_period = is_trial_period
            subscription.save()

    def process_itunes_receipt(
        self, user, itunes_receipt, log_purchase=True,
    ):
        '''
        Subscribes if valid.

        Will raise InvalidReceipt error if invalid.
        '''
        if log_purchase:
            log_item = InAppPurchaseLogItem.objects.create(
                subscriber=user,
                itunes_receipt=itunes_receipt,
            )

        response = itunesiap.verify(
            itunes_receipt,
            password=settings.ITUNES_SHARED_SECRET,
            env=itunesiap.env.review)
        latest_receipt_info = response.latest_receipt_info[-1]

        original_transaction_id = (
            latest_receipt_info['original_transaction_id'])
        is_trial_period = (
            latest_receipt_info['is_trial_period'].lower() == 'true')

        if log_purchase:
            log_item.original_transaction_id = original_transaction_id
            log_item.save()

        self.model.objects.subscribe(
            user,
            original_transaction_id,
            _receipt_date_to_datetime(latest_receipt_info['expires_date_ms']),
            is_trial_period=is_trial_period,
        )

        logger.info('Processed iTunes receipt')

    def process_itunes_subscription_update_notification(self, notification):
        '''
        Will raise InvalidReceipt error if invalid.
        '''
        shared_secret = notification['password']
        if shared_secret != settings.ITUNES_SHARED_SECRET:
            raise PermissionDenied('Invalid iTunes shared secret.')

        receipt_info = notification.get(
            'latest_receipt_info', notification['latest_expired_receipt_info'])
        SubscriptionUpdateNotificationLogItem.objects.create(
            receipt_info=receipt_info,
            original_transaction_id=
                notification['latest_receipt_info']['original_transaction_id'])

        if notification['environment'] == 'PROD':
            environment = itunesiap.env.production
        else:
            environment = itunesiap.env.sandbox

        notification_type = notification['notification_type']

        if notification_type in [
            'RENEWAL', 'INTERACTIVE_RENEWAL',
        ]:
            receipt = notification['latest_receipt']
            itunesiap.verify(receipt, password=settings.ITUNES_SHARED_SECRET)

            original_transaction_id = receipt_info['original_transaction_id']

            subscription = Subscription.objects.get(
                original_transaction_id=original_transaction_id)
            subscription.active = True
        elif notification_type == 'CANCEL':
            receipt = itunes_receipt['latest_expired_receipt']

            itunesiap.verify(receipt, password=settings.ITUNES_SHARED_SECRET)

            original_transaction_id = receipt_info['original_transaction_id']

            subscription = Subscription.objects.get(
                original_transaction_id=original_transaction_id)
            subscription.active = False
        elif notification_type == 'DID_CHANGE_RENEWAL_PREF':
            # Customer changed the plan that takes affect at the next
            # subscription renewal. Current active plan is not affected.
            return
        elif notification_type == 'INITIAL_BUY':
            # Doesn't have an original_transaction_id yet so it's useless.
            # See https://forums.developer.apple.com/thread/98799
            return

        subscription.sandbox = environment == itunesiap.env.sandbox
        subscription.latest_itunes_receipt = receipt
        subscription.expires_date = _receipt_date_to_datetime(
            receipt_info['expires_date'])
        subscription.is_trial_period = (
            receipt_info['is_trial_period'].lower() == 'true')
        subscription.save()

        logger.info('Processed iTunes subscription update notification')


class Subscription(models.Model):
    objects = SubscriptionManager()

    subscriber = models.ForeignKey(
        User, models.CASCADE, unique=True, db_index=True, editable=False)

    expires_date = models.DateTimeField()
    active = models.BooleanField(default=True, blank=True)
    is_trial_period = models.BooleanField(default=False, blank=True)
    sandbox = models.BooleanField(default=False, blank=True)

    original_transaction_id = models.CharField(max_length=300)
    latest_itunes_receipt = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ['-created_at']


class InAppPurchaseLogItem(models.Model):
    itunes_receipt = models.TextField(editable=False)
    subscriber = models.ForeignKey(User, models.CASCADE, editable=False)
    original_transaction_id = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def process_itunes_receipt(self):
        '''
        Useful for replaying a transaction that failed due to a bug.
        '''
        Subscription.objects.process_itunes_receipt(
            self.subscriber, self.itunes_receipt, log_purchase=False)

    class Meta:
        ordering = ['-created_at']


class SubscriptionUpdateNotificationLogItem(models.Model):
    receipt_info = JSONField(editable=False)
    original_transaction_id = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ['-created_at']
