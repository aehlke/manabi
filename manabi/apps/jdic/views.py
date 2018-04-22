import httplib

from django.conf import settings
from django.views.decorators.http import require_POST

from manabi.apps.flashcards.views.decorators import flashcard_api as api
from manabi.apps.flashcards.views.decorators import ApiException


@api
#@require_POST
def audio_file_exists(request):
    '''
    Returns true or false, depending on whether the given filename exists
    on the JDic audio server.

    `filename` must be in the POST parameters.
    '''
    #TODO-OLD
    return False

    filename = request.POST['filename']

    conn = httplib.HTTPConnection(
        settings.JDIC_AUDIO_SERVER_URL.lstrip('http://').rstrip('/audio/'),
        timeout=settings.JDIC_AUDIO_SERVER_TIMEOUT)

    url = ''.join(['/audio/', filename])

    conn.request('HEAD', url)
    res = conn.getresponse()
    conn.close()

    if res.status == 200:
        return True
    elif res.status == 404:
        return False
    else:
        raise ApiException('Error communicating with JDic audio server.'
                            ' (HTTP {})'.format(res.status))
