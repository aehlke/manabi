from django.conf import settings


def url_prefixes(request):
    return {
        'DEFAULT_URL_PREFIX': settings.DEFAULT_URL_PREFIX,
        'API_URL_PREFIX': settings.API_URL_PREFIX,
        'BRANCH_KEY': settings.BRANCH_KEY,
    }
