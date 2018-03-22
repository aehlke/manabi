from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def save_feed(feed_filename, feed_xml):
    default_storage.save(
        'feeds/{}'.format(feed_filename), ContentFile(feed_xml))
