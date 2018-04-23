from django.template import RequestContext
from django.shortcuts import render_to_response


class JsonDebugMiddleware:
    def process_response(self, request, response):
        if 'DEBUG' in request.GET and 'json' in response['Content-Type']:
            content = response.content
            #response['Content-Type'] = 'text/html'
            return render_to_response('json_debug.html', {
                'json': content
            }, context_instance=RequestContext(request))
        return response


# http://stackoverflow.com/questions/20534577/
class WakeRequestUserMiddleware:
    def process_request(self, request):
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
