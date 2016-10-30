from rest_framework import serializers


class ManabiModelSerializer(serializers.ModelSerializer):
    pass


# From https://github.com/tomchristie/django-rest-framework/issues/1985#issuecomment-61871134
class FilterRelatedMixin(object):
    def __init__(self, *args, **kwargs):
        super(FilterRelatedMixin, self).__init__(*args, **kwargs)

        for name, field in self.fields.iteritems():
            if (
                isinstance(field, serializers.RelatedField)
                or isinstance(field, serializers.ModelSerializer)
            ):
                method_name = 'filter_{}'.format(name)
                try:
                    func = getattr(self, method_name)
                except AttributeError:
                    pass
                else:
                    field.queryset = func(field.queryset)
