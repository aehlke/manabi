from rest_framework.validators import UniqueValidator

from manabi.api.serializers import ManabiModelSerializer
from manabi.apps.reader_sources.models import ReaderSource


class ReaderSourceSerializer(ManabiModelSerializer):
    # https://stackoverflow.com/a/32452603/89373
    def run_validators(self, value):
        '''
        Gets rid of the source_url uniqueness constraint during validation,
        as we will get_or_create the record.
        '''
        for validator in self.validators:
            if isinstance(validator, UniqueValidator):
                self.validators.remove(validator)
        super(ReaderSourceSerializer, self).run_validators(value)

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
