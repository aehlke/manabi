from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def save_feed(feed_filename, feed_xml):
    path = 'feeds/{}'.format(feed_filename)

    if default_storage.exists(path):
        default_storage.delete(path)

    default_storage.save(path, ContentFile(feed_xml))
