import pytz


class UserTimezoneMiddleware(object):
    def process_request(self, request):
        request.user_timezone = pytz.timezone(
            request.META.get('HTTP_X_TIME_ZONE', 'America/New_York'))
