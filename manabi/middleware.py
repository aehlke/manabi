import pytz


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_timezone = pytz.timezone(
            request.META.get('HTTP_X_TIME_ZONE', 'America/New_York'))

        return self.get_response(request)
