# -*- coding: utf-8 -*-

import logging
import os
import os.path
import posixpath
import sys
from socket import gethostname


LIVE_HOST = os.path.isfile('/etc/manabi/production')

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DEBUG = not LIVE_HOST

USE_TEST_STUBS = False

ALLOWED_HOSTS = ['.manabi.io', '127.0.0.1']

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

USE_X_FORWARDED_HOST = True

STATIC_ROOT = None
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static'),
]
MEDIA_URL = '/media/'
# FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
# FILE_UPLOAD_PERMISSIONS = 0o755
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

def whitenoise_add_headers(headers, path, url):
    if path.endswith('.rss'):
        MAX_AGE = 60 * 60 * 4
        STALE_WHILE_REVALIDATE = 60 * 60 * 24 * 2
        headers['Cache-Control'] = (
            'max-age={}, stale-while-revalidate={}, stale-if-error={}, public'
            .format(MAX_AGE, STALE_WHILE_REVALIDATE, STALE_WHILE_REVALIDATE))
WHITENOISE_ADD_HEADERS_FUNCTION = whitenoise_add_headers
WHITENOISE_MIMETYPES = {'.rss': 'application/rss+xml'}
WHITENOISE_CHARSET = 'utf-8'

ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, 'admin/')
SECRET_KEY = 'secret-key-only-used-for-development-do-not-use-in-production'

TEMPLATES = [
    {
        'BACKEND': 'manabi.jinja2_backend.ManabiJinja2',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'templates'),
            os.path.join(PROJECT_ROOT, 'apps/flashcards/templates'),
            os.path.join(PROJECT_ROOT, 'apps/profiles/templates'),
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'manabi.context_processors.url_prefixes',
            ],
            'environment': 'manabi.jinja2_environment.environment',
            'extensions': [
                'jinja2.ext.autoescape',
                'jinja2.ext.i18n',
                'jinja2.ext.with_',
                'webpack_loader.contrib.jinja2ext.WebpackExtension',
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',

    'django.middleware.common.CommonMiddleware',

    'manabi.middleware.UserTimezoneMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'silk.middleware.SilkyMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    #'account.middleware.LocaleMiddleware', #Enable when we add more translations.
    #'django.middleware.doc.XViewMiddleware',
    #'pagination.middleware.PaginationMiddleware',
    #'pinax.middleware.security.HideSensistiveFieldsMiddleware',
    'manabi.apps.utils.middleware.WakeRequestUserMiddleware',
)


# Potentially too slow at scale, but we used to have this via
# TransactionMiddleware.
ATOMIC_REQUESTS = True


if DEBUG:
    MIDDLEWARE_CLASSES += (
        #'debug_toolbar.middleware.DebugToolbarMiddleware',
        'manabi.apps.utils.middleware.JsonDebugMiddleware',
    )

SILKY_MAX_REQUEST_BODY_SIZE = 128  # kb
SILKY_MAX_RESPONSE_BODY_SIZE = 128  # kb
SILKY_META = True  # See what effect Silk had on DB time.
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_MAX_RECORDED_REQUESTS = 9000
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 1
def silk_intercept(request):
    if request.user.is_anonymous():
        return False
    if request.user.username not in ['alextest', 'alex']:
        return False
    return not request.path.startswith('/admin/') and request.path != '/'
SILKY_INTERCEPT_FUNC = silk_intercept

ROOT_URLCONF = 'manabi.urls'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.humanize',
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

    # Auth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.twitter',

    # Other
    'rest_framework',
    'rest_framework.authtoken',
    'adminsortable',
    'cachecow',
    'catnap',
    'crispy_forms',  # For browsable API.
    'django_nose',
    'django_rq',

    'djoser',

    # django-rest-framework-social-oauth2
    'oauth2_provider',
    'social_django',
    'rest_framework_social_oauth2',

    'raven.contrib.django.raven_compat',
    'silk',
    'webpack_loader',

    # My own.
    'manabi.apps.flashcards',
    'manabi.apps.featured_decks',
    'manabi.apps.books',
    'manabi.apps.utils',
    'manabi.apps.jdic',
    'manabi.apps.manabi_auth',
    'manabi.apps.manabi_redis',
    'manabi.apps.profiles',
    'manabi.apps.reader_feeds',
    'manabi.apps.reader_sources',
    'manabi.apps.reading_level',
    'manabi.apps.review_results',
    'manabi.apps.subscriptions',
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

# Test runner config.
if 'test' in sys.argv:
    for queue_config in RQ_QUEUES.values():
        queue_config['ASYNC'] = False
    MIDDLEWARE_CLASSES = tuple(
        cls_path for cls_path in MIDDLEWARE_CLASSES
        if 'silk.middleware' not in cls_path
    )
    INSTALLED_APPS = tuple(
        app_path for app_path in INSTALLED_APPS
        if app_path != 'silk'
    )

    class DisableMigrations(object):
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return None
    MIGRATION_MODULES = DisableMigrations()


#TODO fix, not working
SHELL_PLUS_POST_IMPORTS = (
    ('django.db.models', 'Q'),
)

#TODELETE
ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda o: '/profiles/profile/%s/' % o.username,
}


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id, name, email'}

DJOSER = {
    'SERIALIZERS': {
        'user_create':
        'manabi.apps.manabi_auth.serializers.UserCreateWithTokenSerializer',
    },
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': ['https://manabi.io/'],
}

# django-allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 10
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_USERNAME_BLACKLIST = [
    'admin', 'administrator', 'alex', 'alexe', 'aehlke', 'manabi', 'manabio', 'master',
    'owner', 'manabiorg', 'manabi.io', 'alexehlke', 'ehlke', 'anki',
]
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False

BASIC_AUTH_CHALLENGE = 'Manabi'
BASIC_AUTH_REALM = 'manabi'

SITE_NAME = 'Manabi'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URLNAME = 'homepage'

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
MECAB_RC_PATH = '/usr/local/etc/mecabrc'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'js/bundles/',  # must end with slash
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'static/js/webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map'],
    }
}
if not DEBUG:
    WEBPACK_LOADER['DEFAULT'].update({
        'BUNDLE_DIR_NAME': 'js/dist/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'static/js/webpack-stats-prod.json')
    })

BRANCH_KEY = 'key_live_oeAeGJl13FZd3GdCrS2FXbiiyDgsH2KI'

DEFAULT_URL_PREFIX = 'http://192.168.0.1:8000'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'UNICODE_JSON': False,
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
        raise Exception("Couldn't import development settings.")


CACHES['default']['KEY_PREFIX'] = '2'
