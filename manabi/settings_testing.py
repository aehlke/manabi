from manabi.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'manabi_testing',
        'USER': 'testing',
        'PASSWORD': 'testing',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

import logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(message)s')
