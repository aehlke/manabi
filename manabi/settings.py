# -*- coding: utf-8 -*-

import logging
import os
import os.path
import posixpath
import sys
from socket import gethostname


LIVE_HOST = os.path.isfile('/etc/manabi/production')

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = not LIVE_HOST

USE_TEST_STUBS = False

ALLOWED_HOSTS = ['.manabi.io']

INTERNAL_IPS = (
    '127.0.0.1',
)

ADMINS = (
    ('alex', 'alex.ehlke@gmail.com'),
)

if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
            },
            'simple': {
                'format': '%(levelname)s %(message)s',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
         'root': {
             'handlers': ['console'],
             'level': logging.WARNING,
        },
        'loggers': {
            'manabi': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
            'django.request': {
                'handlers': ['console'],
                'propagate': True,
                'level': 'DEBUG',
            },
        },
    }
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
            },
            'simple': {
                'format': '%(levelname)s %(message)s',
            },
        },
        'handlers': {
            'console': {
                'level': 'WARNING',
                'class': 'logging.StreamHandler',
            },
        },
         'root': {
             'handlers': ['console'],
             'level': logging.WARNING,
        },
        'loggers': {
            'manabi': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'django.request': {
                'handlers': ['console'],
                'propagate': True,
                'level': 'WARNING',
            },
        },
    }

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en'
SITE_ID = 1
USE_I18N = False

if LIVE_HOST:
    SITE_MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media')
else:
    SITE_MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media')

USE_X_FORWARDED_HOST = True

STATIC_ROOT = os.path.join(SITE_MEDIA_ROOT, 'static')
STATIC_URL = '/site_media/static/'

# Additional directories which hold static files
#import uni_form
#STATICFILES_DIRS = (
#    #('basic_project', os.path.join(PROJECT_ROOT, 'media')),
#    ('pinax', os.path.join(PINAX_ROOT, 'media', PINAX_THEME)),
#    os.path.join(PROJECT_ROOT, 'static'),
#    os.path.join(PINAX_ROOT, 'media', PINAX_THEME),
#    os.path.join(uni_form.__path__[0], 'media'),
#)

ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, 'admin/')
SECRET_KEY = 'secret-key-only-used-for-development-do-not-use-in-production'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'templates')],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ]
    },
}]
if LIVE_HOST:
    TEMPLATES[0]['APP_DIRS'] = False
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',

    # 'silk.middleware.SilkyMiddleware',

    'django.middleware.common.CommonMiddleware',

    'catnap.middleware.HttpExceptionMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'catnap.basic_auth.BasicAuthMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    #'account.middleware.LocaleMiddleware', #Enable when we add more translations.
    #'django.middleware.doc.XViewMiddleware',
    #'pagination.middleware.PaginationMiddleware',
    #'pinax.middleware.security.HideSensistiveFieldsMiddleware',
    'manabi.apps.utils.middleware.WakeRequestUserMiddleware',
    'catnap.middleware.HttpAcceptMiddleware',
    'catnap.middleware.HttpMethodsFallbackMiddleware',
)


# Potentially too slow at scale, but we used to have this via
# TransactionMiddleware.
ATOMIC_REQUESTS = True


if DEBUG:
    MIDDLEWARE_CLASSES += (
        #'debug_toolbar.middleware.DebugToolbarMiddleware',
        'manabi.apps.utils.middleware.JsonDebugMiddleware',
    )


ROOT_URLCONF = 'manabi.urls'

#  TEMPLATE_CONTEXT_PROCESSORS = (
#      'django.contrib.auth.context_processors.auth',
#      'django.core.context_processors.request',
#      'django.core.context_processors.debug',
#      'django.core.context_processors.i18n',
#      'django.core.context_processors.media',
#      'django.core.context_processors.static',
#      'django.contrib.messages.context_processors.messages',
#
#      #'staticfiles.context_processors.static_url',
#      #"pinax.core.context_processors.pinax_settings",
#      #'pinax.apps.account.context_processors.account',
#      #'notification.context_processors.notification',
#      #'announcements.context_processors.site_wide_announcements',
#
#      #'dojango.context_processors.config',
#      #'manabi.context_processors.site_base_extender',
#  )

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.humanize',
)

INSTALLED_APPS += (
    'django.contrib.staticfiles',

    # external
    #'notification', # must be first
    #'emailconfirmation',
    #'mailer',
    #'announcements',
    #'pagination',
    'timezones',
    #'ajax_validation',
    #'uni_form',

    'django_extensions',

    # Other
    'rest_framework',
    'crispy_forms',  # For browsable API.
    'django_nose',
    'lazysignup',
    'catnap',
    'cachecow',
    'django_rq',
    'djoser',
    # 'silk',
    'raven.contrib.django.raven_compat',

    # My own.
    'manabi.apps.flashcards',
    'manabi.apps.books',
    'manabi.apps.utils',
    'manabi.apps.jdic',
    'manabi.apps.manabi_redis',
    'manabi.apps.reading_level',
    'manabi.apps.twitter_usages',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_PLUGINS = [
    'manabi.nose_plugins.SilenceSouth',
]
NOSE_ARGS = ['--logging-level=WARNING']

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 9,  # kyuu
        'DEFAULT_TIMEOUT': 360,
    },
}
if 'test' in sys.argv:
    for queue_config in RQ_QUEUES.values():
        queue_config['ASYNC'] = False


#TODO fix, not working
SHELL_PLUS_POST_IMPORTS = (
    ('django.db.models', 'Q'),
)

#TODELETE
ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda o: '/profiles/profile/%s/' % o.username,
}


ACCOUNT_EMAIL_VERIFICATION = False

AUTHENTICATION_BACKENDS = [
    #'pinax.apps.account.auth_backends.AuthenticationBackend',
    #'utils.auth_backends.AuthenticationBackendWithLazySignup',
    'django.contrib.auth.backends.ModelBackend',
    'lazysignup.backends.LazySignupBackend',
]

BASIC_AUTH_CHALLENGE = 'Manabi'
BASIC_AUTH_REALM = 'manabi'

LAZYSIGNUP_ENABLE = False

SITE_NAME = 'Manabi'

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URLNAME = 'home'

DEFAULT_FROM_EMAIL = 'Manabi <support@manabi.io>'

FIXTURE_DIRS = (
    'fixtures/',
)

# JDic audio server root URL - the directory containing the mp3s.
# Must end in '/'
#TODO-OLD
JDIC_AUDIO_SERVER_URL = 'http://jdic.manabi.org/audio/'
JDIC_AUDIO_SERVER_TIMEOUT = 6 # seconds

START_OF_DAY = 5 # hour of day most likely to be while the user is asleep, localized

MECAB_ENCODING = 'utf8'


if LIVE_HOST:
    DEFAULT_URL_PREFIX = 'https://manabi.io'
else:
    #DEFAULT_URL_PREFIX = 'http://192.168.2.127:8000'
    DEFAULT_URL_PREFIX = 'http://192.168.0.1:8000'

#sudo su postgres -c psql template1


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    # Requires using model permissions, not ready for this yet...
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    # ],
    # 'PAGE_SIZE': 100,
}


if LIVE_HOST:
    try:
        from manabi.settings_production_secrets import *
        from manabi.settings_production import *
    except ImportError:
        pass
elif os.environ.get('CIRCLECI'):
    from manabi.settings_circleci import *
else:
    try:
        from manabi.settings_development_secrets import *
        from manabi.settings_development import *
    except ImportError:
        pass
