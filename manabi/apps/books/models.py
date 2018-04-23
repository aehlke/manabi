from functools import wraps
from urllib.error import URLError

from django.db import models
#from amazonproduct import API as AmazonAPI

from manabi.apps.utils.slugs import slugify
from django.conf import settings


#TODO-OLD find different way.
#amazon_api = AmazonAPI(settings.AWS_KEY, settings.AWS_SECRET_KEY, 'us')


class DeckedTextbookManager(models.Manager):
    def get_query_set(self):
        return super(DeckedTextbookManager, self).get_query_set().filter(
                deck__active=True, deck__shared=True).distinct()


def uses_amazon_api(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if not self.isbn:
            raise Exception('Textbook has no ISBN.')
        return func(self, *args, **kwargs)
    return wrapped


class Textbook(models.Model):
    objects = models.Manager()
    decked_objects = DeckedTextbookManager()

    slug = models.SlugField(blank=True) # Defaults to max_length=50
    isbn = models.CharField(max_length=13)
    custom_title = models.CharField(max_length=200, blank=True,
            help_text='Set this to override the Amazon product name.')

    #TODO-OLD student level field

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        try:
            return self.get_basic_info()['title'] + ' [{0}]'.format(self.isbn)
        except URLError:
            return 'ISBN: {0}'.format(self.isbn)

    def save(self, *args, **kwargs):
        title = self.get_basic_info()['title']
        self.slug = slugify(title)
        super(Textbook, self).save(*args, **kwargs)

    @property
    def shared_decks(self):
        return self.deck_set.filter(
                active=True, shared=True)

    @models.permalink
    def get_absolute_url(self):
        if self.slug:
            return ('book_detail_with_slug', (), {
                'object_id': self.id,
                'slug': self.slug,
            })
        else:
            return ('book_detail_without_slug', (), {
                'object_id': self.id,
            })

    @property
    def cleaned_isbn(self):
        return self.isbn.strip().replace('-', '')

    def _item_lookup(self, **kwargs):
        return
        #TODO-OLD fix
        return amazon_api.item_lookup(
                self.cleaned_isbn, IdType='ISBN', SearchIndex='Books', **kwargs)

    @uses_amazon_api
    def get_image_urls(self):
        '''
        Returns a dict with each available image size:
            {'size': 'url'}
        '''
        urls = {}
        root = self._item_lookup(ResponseGroup='Images')
        for size in ('Small', 'Medium', 'Large'):
            urls[size.lower()] = getattr(root.Items.Item, size + 'Image').URL.pyval
        return urls

    @uses_amazon_api
    def get_basic_info(self):
        '''
        Returns the following in a dict:
            author
            title
            purchase_url
        '''
        root = self._item_lookup(ResponseGroup='Small')
        attribs = root.Items.Item.ItemAttributes
        return {
            'author': attribs.Author.pyval,
            'title': self.custom_title or attribs.Title.pyval,
        }

