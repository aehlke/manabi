import rq
from django.conf import settings
from raven import Client
from raven.transport.http import HTTPTransport
from rq.contrib.sentry import register_sentry


class ManabiWorker(rq.Worker):
    def __init__(self, *args, **kwargs):
        super(ManabiWorker, self).__init__(*args, **kwargs)

        dsn = settings.RAVEN_CONFIG['dsn']
        client = Client(dsn, transport=HTTPTransport)
        register_sentry(client)
