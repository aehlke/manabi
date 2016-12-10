DEFAULT_URL_PREFIX = 'https://manabi.io'
API_URL_PREFIX = 'https://api.manabi.io'

REDIS = {
    'host': 'localhost',
    'port': 6378,
    'db'  : 0,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

STATIC_ROOT = '/var/www/manabi'

EMAIL_BACKEND = 'sparkpost.django.email_backend.SparkPostEmailBackend'
SPARKPOST_OPTIONS = {
    'track_opens': True,
    'track_clicks': True,
    'transactional': True,
}

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

SILKY_MAX_REQUEST_BODY_SIZE = 128  # kb
SILKY_MAX_RESPONSE_BODY_SIZE = 128  # kb
SILKY_META = True  # See what effect Silk had on DB time.
