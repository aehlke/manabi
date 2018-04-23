import random
from urllib.parse import urljoin

from autoslug import AutoSlugField
from django.conf import settings
from django.db import models


class DeckCollection(models.Model):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='name', always_update=True, unique=False)
    image = models.ImageField(blank=True)
    description = models.TextField(max_length=2000, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        return self.name

    @property
    def image_url(self):
        if self.image:
            url = self.image.url
        else:
            url = '/static/img/deck_icons/waves-{}.jpg'.format(
                (self.synchronized_with_id or self.id) % 8)
        return urljoin(settings.DEFAULT_URL_PREFIX, url)
