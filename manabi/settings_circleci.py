DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'circle_test',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    },
}

REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db'  : 0,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

SILKY_PYTHON_PROFILER = False

TWITTER_APP_KEY = None
TWITTER_APP_SECRET = None
