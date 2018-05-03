from social.backends.facebook import FacebookOAuth2


class FacebookOAuth2ForManabi(FacebookOAuth2):
    name = 'facebook_for_manabi'


class FacebookOAuth2ForManabiReader(FacebookOAuth2):
    name = 'facebook_for_manabi_reader'
