from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from manabi.apps.furigana import inject

@api_view(['POST'])
def inject_furigana(request):
    try:
        text = request.data['text']
    except KeyError:
        raise ValidationError("Must supply text parameter.")

    return Response({'text_with_furigana': inject.inject_furigana(text)})
