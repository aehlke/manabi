from datetime import datetime, timedelta
import logging

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.db import models
import itunesiap

logger = logging.getLogger(__name__)

GRACE_PERIOD = timedelta(days=365)


def _receipt_date_to_datetime(receipt_date):
    return datetime.fromtimestamp(int(receipt_date) / 1000.0)


class OutOfDateReceiptError(ValueError):
    pass


def user_is_active_subscriber(user, with_grace_period=True):
    if not user.is_authenticated:
        return False

    if user.username in settings.FREE_SUBSCRIPTION_USERNAMES:
        return True

    try:
        subscription = Subscription.objects.get(
            subscriber=user,
            active=True,
        )
    except Subscription.DoesNotExist:
        return False

    # Customers on earlier versions of Manabi had bugs with subscriptions.
    if subscription.created_at < datetime(year=2019, month=6, day=1):
        return True

    expires_date = subscription.expires_date
    if with_grace_period:
        expires_date += GRACE_PERIOD

    return expires_date >= datetime.utcnow()


class SubscriptionManager(models.Manager):
    def subscribe(
        self, user, original_transaction_id, expires_date, purchase_date,
        is_trial_period=False,
    ):
        subscription, created = Subscription.objects.get_or_create(
            subscriber=user,
            defaults={
                'expires_date': expires_date,
                'purchase_date': purchase_date,
                'original_transaction_id': original_transaction_id,
            },
        )
        if not created and (
            not subscription.active or subscription.expires_date < expires_date
        ):
            subscription.active = True
            subscription.expires_date = expires_date
            subscription.purchase_date = purchase_date
            subscription.is_trial_period = is_trial_period
            subscription.save()

    def process_itunes_receipt(
        self, user, itunes_receipt, log_purchase=True,
    ):
        '''
        Subscribes if valid.

        If log_purchase is True, will log only if the receipt didn't already
        exist.

        Will raise InvalidReceipt error if invalid. Raises
        OutOfDateReceiptError if not the latest receipt on file.
        '''
        try:
            response = itunesiap.verify(
                itunes_receipt,
                password=settings.ITUNES_SHARED_SECRET,
                env=itunesiap.env.review)
            latest_receipt_info = response.latest_receipt_info[-1]
        except Exception as e:
            InAppPurchaseLogItem.objects.get_or_create(
                subscriber=user,
                itunes_receipt=itunes_receipt,
            )
            raise e from None

        original_transaction_id = (
            latest_receipt_info['original_transaction_id'])
        is_trial_period = (
            latest_receipt_info['is_trial_period'].lower() == 'true')
        purchase_date = _receipt_date_to_datetime(
            latest_receipt_info['purchase_date_ms'])

        # Confirm this incoming receipt isn't older than one on file.
        try:
            existing_subscription = Subscription.objects.get(
                original_transaction_id=original_transaction_id)

            existing_purchase_date = existing_subscription.purchase_date
            if (
                existing_purchase_date is not None
                and purchase_date > existing_purchase_date
            ):
                raise OutOfDateReceiptError()
        except Subscription.DoesNotExist:
            pass

        if log_purchase:
            InAppPurchaseLogItem.objects.get_or_create(
                subscriber=user,
                itunes_receipt=itunes_receipt,
                original_transaction_id=original_transaction_id,
            )

        self.model.objects.subscribe(
            user,
            original_transaction_id,
            _receipt_date_to_datetime(latest_receipt_info['expires_date_ms']),
            purchase_date,
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

        try:
            receipt_info = notification['latest_receipt_info']
        except KeyError:
            receipt_info = notification['latest_expired_receipt_info']

        notification_type = notification['notification_type']

        SubscriptionUpdateNotificationLogItem.objects.create(
            production_environment=(notification['environment'] == 'PROD'),
            notification_type=notification_type,
            receipt_info=receipt_info,
            original_transaction_id=
                receipt_info['original_transaction_id'])

        if notification['environment'] == 'PROD':
            environment = itunesiap.env.production
        else:
            environment = itunesiap.env.sandbox

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
        elif notification_type == 'DID_CHANGE_RENEWAL_STATUS':
            # Indicates a change in the subscription renewal status.
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

    subscriber = models.OneToOneField(
        User, models.CASCADE, db_index=True, editable=False)

    expires_date = models.DateTimeField()
    active = models.BooleanField(default=True, blank=True)
    is_trial_period = models.BooleanField(default=False, blank=True)
    sandbox = models.BooleanField(default=False, blank=True)
    purchase_date = models.DateTimeField(null=True, blank=True)

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
    notification_type = models.CharField(max_length=40, blank=True)
    production_environment = models.BooleanField(default=True)
    receipt_info = JSONField(editable=False)
    original_transaction_id = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ['-created_at']


class PurchasedSubscriptionProduct:
    def __init__(self, user, itunes_receipt):
        self._user = user
        self.itunes_receipt = itunes_receipt

    def subscription_is_active(self):
        return user_is_active_subscriber(self._user)
