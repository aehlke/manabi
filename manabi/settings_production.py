DEFAULT_URL_PREFIX = 'https://manabi.io'
API_URL_PREFIX = 'https://api.manabi.io'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

STATIC_ROOT = '/var/www/manabi'
MEDIA_ROOT = '/var/www/manabi_media'

EMAIL_BACKEND = 'sparkpost.django.email_backend.SparkPostEmailBackend'
SPARKPOST_OPTIONS = {
    'track_opens': True,
    'track_clicks': True,
    'transactional': True,
}

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
