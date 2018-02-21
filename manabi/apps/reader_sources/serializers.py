from rest_framework.validators import UniqueValidator

from manabi.api.serializers import ManabiModelSerializer
from manabi.apps.reader_sources.models import ReaderSource


class ReaderSourceSerializer(ManabiModelSerializer):
    class Meta:
        model = ReaderSource
        fields = (
            'id',
            'source_url',
            'title',
            'thumbnail_url',
        )
        reader_only_fields = (
            'id',
        )
        # https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
        extra_kwargs = {
            'source_url': {
                'validators': [],
            }
        }
