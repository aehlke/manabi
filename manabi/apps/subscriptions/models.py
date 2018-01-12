from django.contrib.auth.models import User
from django.db import models
import itunesiap


class SubscriptionManager(models.Manager):
    def subscribe(self, user):
        subscription, created = Subscription.objects.get_or_create(
            subscriber=request.user,
        )
        if not created and not subscription.active:
            subscription.active = True
            subscription.save()

    def process_itunes_receipt(self, user, itunes_receipt):
        '''
        Will raise InvalidReceipt error if invalid.
        '''
        response = itunesiap.verify(itunes_receipt)
        self.model.objects.subscribe(user)


class Subscription(models.Model):
    objects = SubscriptionManager()

    subscriber = models.ForeignKey(
        User, unique=True, db_index=True, editable=False)

    active = models.BooleanField(default=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
