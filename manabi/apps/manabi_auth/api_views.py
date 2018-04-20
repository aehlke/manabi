from django.contrib.auth import user_logged_in
from djoser.views import UserCreateView
from djoser.utils import login_user


class UserCreateWithTokenView(UserCreateView):
    def perform_create(self, serializer):
        super(UserCreateWithTokenView, self).perform_create(serializer)

        user = serializer.instance
        user_logged_in.send(
            sender=user.__class__, request=self.request, user=user)
