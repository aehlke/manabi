import base64
import hashlib
import hmac
from urllib import parse

from rest_framework.decorators import api_view
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView
from requests.exceptions import HTTPError
from social_django.utils import psa

from manabi.apps.manabi_auth.models import (
    AppleIDAccount,
    generate_username_for_apple_id,
)
from manabi.apps.manabi_auth.serializers import (
    SignInWithAppleIDSerializer,
    SocialAccessTokenSerializer,
)


@api_view(http_method_names=['POST'])
@permission_classes([AllowAny])
def sign_in_with_apple_id(request):
    serializer = SignInWithAppleIDSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        account = AppleIDAccount.objects.get(
            user_identifier=serializer.user_identifier)
        user = account.user
    except AppleIDAccount.DoesNotExist:
        username = generate_username_for_apple_id(
            serializer.user_identifier,
            serializer.first_name)
        user = User.objects.create_user(
            username=username,
            email=serializer.email,
            first_name=serializer.first_name,
            last_name=serializer.last_name,
        )
        account = AppleIDAccount.objects.create(
            user=user,
            user_identifier=serializer.user_identifier,
        )

    if user.is_active:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'auth_token': token.key,
            'username': user.username,
        })
    else:
        return Response(
            {'errors': {nfe: 'This user account is inactive'}},
            status=status.HTTP_400_BAD_REQUEST,
        )


# See: https://gist.github.com/anindyaspaul/c9d4650e8ffd4f133e393a57ddc21616
class DiscourseSSOView(APIView):
	"""
	Single Sign On view for Discourse forum

	The view returns the required payload and signature for discourse.
	These payloads have to be urlencoded by the client and passed as
	query parameter to the discourse sso login url.

	Signature validation depends on settings.SECRET_KEY.
	Add this as the secret key in discourse sso settings.

	References:
	- https://meta.discourse.org/t/sso-example-for-django/14258
	- https://gist.github.com/alee/3c6161809ef78966454e434a8ed350d1
	"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Query params:
        - sso: Single Sign On payload
        - sig: Signature
        """

        payload = request.query_params.get('sso')
        signature = request.query_params.get('sig')

        if None in [payload, signature]:
            raise ParseError('No SSO payload or signature. Please contact support if this problem persists.')

        # Validate the payload
        payload = bytes(parse.unquote(payload), encoding='utf-8')
        decoded = base64.decodebytes(payload).decode('utf-8')
        if len(payload) == 0 or 'nonce' not in decoded:
            raise ParseError('Invalid payload. Please contact support if this problem persists.')

        key = bytes(settings.SECRET_KEY, encoding='utf-8')  # must not be unicode
        h = hmac.new(key, payload, digestmod=hashlib.sha256)
        this_signature = h.hexdigest()
        if not hmac.compare_digest(this_signature, signature):
            raise ParseError('Invalid payload. Please contact support if this problem persists.')

        # Build the return payload
        qs = parse.parse_qs(decoded)
        user = request.user
        params = {
            'nonce': qs['nonce'][0],
            'email': user.email,
            'external_id': user.id,
            'username': user.username,
        }
        return_payload = base64.encodebytes(bytes(parse.urlencode(params), 'utf-8'))
        h = hmac.new(key, return_payload, digestmod=hashlib.sha256)
        return_sig = h.hexdigest()

        # Redirect back to Discourse
        # query_string = parse.urlencode({'sso': return_payload, 'sig': return_sig})
        # discourse_sso_url = '{0}/session/sso_login?{1}'.format("", query_string)

        return Response(
            data={
                'sso': return_payload,
                'sig': return_sig
            }
        )


# See: https://www.toptal.com/django/integrate-oauth-2-into-django-drf-back-end
@api_view(http_method_names=['POST'])
@permission_classes([AllowAny])
@psa()
def exchange_token(request, backend):
    '''
    Exchange an OAuth2 access token for one for this site.
    This simply defers the entire OAuth2 process to the front end.
    The front end becomes responsible for handling the entirety of the
    OAuth2 process; we just step in at the end and use the access token
    to populate some user identity.
    The URL at which this view lives must include a backend field, like:
        url(API_ROOT + r'social/(?P<backend>[^/]+)/$', exchange_token),
    Using that example, you could call this endpoint using i.e.
        POST API_ROOT + 'social/facebook/'
        POST API_ROOT + 'social/google-oauth2/'
    Note that those endpoint examples are verbatim according to the
    PSA backends which we configured in settings.py. If you wish to enable
    other social authentication backends, they'll get their own endpoints
    automatically according to PSA.
    ## Request format
    Requests must include the following field
    - `access_token`: The OAuth2 access token provided by the provider
    '''
    serializer = SocialAccessTokenSerializer(data=request.data)

    if serializer.is_valid(raise_exception=True):
        # set up non-field errors key
        # http://www.django-rest-framework.org/api-guide/exceptions/#exception-handling-in-rest-framework-views
        try:
            nfe = settings.NON_FIELD_ERRORS_KEY
        except AttributeError:
            nfe = 'non_field_errors'

        try:
            # this line, plus the psa decorator above, are all that's
            # necessary to get and populate a user object for any properly
            # enabled/configured backend which python-social-auth can handle.
            user = request.backend.do_auth(serializer.validated_data['access_token'])
        except HTTPError as e:
            # An HTTPError bubbled up from the request to the social auth
            # provider. This happens, at least in Google's case, every time
            # you send a malformed or incorrect access key.
            return Response(
                {'errors': {
                    'token': 'Invalid token',
                    'detail': str(e),
                }},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user:
            if user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'auth_token': token.key,
                    'username': user.username,
                })
            else:
                # user is not active; at some point they deleted their account,
                # or were banned by a superuser. They can't just log in with
                # their normal credentials anymore, so they can't log in with
                # social credentials either.
                return Response(
                    {'errors': {nfe: 'This user account is inactive'}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Unfortunately, PSA swallows any information the backend provider
            # generated as to why specifically the authentication failed;
            # this makes it tough to debug except by examining the server logs.
            return Response(
                {'errors': {nfe: "Authentication Failed"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
