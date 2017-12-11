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
