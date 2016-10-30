DEFAULT_URL_PREFIX = 'https://manabi.io'

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

WEBPACK_LOADER.update({
    'BUNDLE_DIR_NAME': 'dist/',
    'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats-prod.json')
})
