from datetime import datetime

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.views import APIView

from manabi.apps.review_results.models import (
    ReviewResults,
)
from manabi.apps.review_results.serializers import (
    ReviewResultsSerializer,
)


class ReviewResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        try:
            review_began_at = datetime.fromtimestamp(float(
                request.query_params['review_began_at']))
        except (ValueError, KeyError):
            raise ValidationError("Invalid or missing review_began_at param.")

        review_results = ReviewResults(
            request.user,
            review_began_at,
        )
        return Response(ReviewResultsSerializer(review_results).data)
