from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from flashcards.models.decks import Deck
from dojango.util import to_json_response, json_encode
from dojango.decorators import json_response
from django.http import HttpResponseServerError, HttpResponse
from django.utils import simplejson as json
import usertagging
from django.conf import settings
import datetime

#decorator_with_arguments = lambda decorator: lambda *args, **kwargs: lambda func: decorator(func, *args, **kwargs)


def all_http_methods(view_func):
    '''
    Decorator that adds headers to a response so that it will
    never be cached.
    '''
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        #modified_request = request #shallow copy is enough
        if request.method == 'POST':
            if '_method' in request.POST and request.POST['_method'] in ['PUT', 'DELETE', 'GET', 'POST']:
                method = request.POST['_method']
                request.method = method
        return view_func(request, *args, **kwargs)
    return wrapper


def has_card_query_filters(func):
    '''
    Adds some kwargs to the `func` call for cleaning request GET data into
    querysets.

    Adds the following (potentially with value None):
        `deck`, `tags`
    '''
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Deck
        if 'deck' in request.GET and request.GET['deck'].strip():
            deck = get_object_or_404(Deck, pk=request.GET['deck'])
        else:
            deck = None
        kwargs['deck'] = deck

        # Tags
        try:
            #TODO support for multiple tags
            tag_id = int(request.GET.get('tags',
                request.GET.get('tag', -1)))
        except ValueError:
            tag_id = -1
        if tag_id != -1:
            tag_ids = [tag_id] #TODO support multiple tags
            tags = usertagging.models.Tag.objects.filter(id__in=tag_ids)
        else:
            tags = None
        kwargs['tags'] = tags

        return func(request, *args, **kwargs)

    return wrapper




class ApiException(Exception):
    '''
    `api_data_response` catches these exceptions and does the following:

    When a view decorated with `api_data_response` raises this exception,
    it results in the 'success' field of the returned JSON data being 
    set to False, and the 'error' field set to the message of the 
    raised exception. 
    '''
    pass


def api_data_response(view_func):
    '''
    Uses `dojango.decorators.json_response`, except with a more 
    specific structure. The view return value is put into the `data` 
    field.

    Ex.:
        {'success': True, 'data': 'foobar'}
    '''
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        ret = {'success': True}

        try:
            ret['data'] = view_func(request, *args, **kwargs)
        except ApiException as e:
            # Wrap our ApiException message in our container format
            ret['success'] = False
            error = e.args
            if len(error) == 1:
                error = error[0]
            ret['error'] = error

        try:
            # Sometimes the serialization fails, i.e. when there are 
            # too deeply nested objects or even classes inside
            json_ret = json_encode(ret)

            # Content-Type header and HTTP response construction
            charset = 'charset={0}'.format(getattr(settings, 'DEFAULT_CHARSET', 'utf-8'))
            content_type = 'application/json'
            content_type = '; '.join([content_type, charset])
            http_ret = HttpResponse(json_ret,
                content_type=content_type)

            # The following are for IE especially
            http_ret['Pragma'] = 'no-cache'
            http_ret['Cache-Control'] = 'must-revalidate'
            http_ret['If-Modified-Since'] = str(datetime.datetime.now())

            return http_ret
        except Exception, e:
            return HttpResponseServerError(content=unicode(e))
    return wrapper


def flashcard_api(view_func):#vendor_subtype=None):
    '''
    DEPRECATED: Will be replaced with new REST stuff.

    Our standard decorator for JSON API views,
    within our flashcard API.

    Uses content-types of form:
        `application/vnd.manabi.flashcards.{{vendor_subtype}}+json`
    Defaults to `application/json`

    It's just a shortcut for decorating with the following:
        `@api_data_response`
        `@login_required`
        `@all_http_methods` #TODO make this middleware?
    '''
    content_type = 'application/json'
    #if content_subtype:
    #    content_type = 'application/vnd.manabi.flashcards.{0}+json'.format(
    #        vendor_subtype)

    return login_required(
           api_data_response(
           all_http_methods(view_func)))


def flashcard_api_with_dojo_data(view_func):
    return json_response(
           login_required(
           all_http_methods(view_func)))


