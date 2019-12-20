import os.path

DEFAULT_URL_PREFIX = 'http://dev.manabi.io:8000'
API_URL_PREFIX = 'http://dev.manabi.io:8000'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'manabi',
        'USER': 'alex',
        'PASSWORD': 'development',
        'HOST': 'localhost',
        'PORT': '5432',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

MEDIA_ROOT = 'media'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SILKY_PYTHON_PROFILER = False

TWITTER_APP_KEY = None
TWITTER_APP_SECRET = None
