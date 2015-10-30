from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template import loader
from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings

from rest_framework import response, status

import jwt
from calendar import timegm
from datetime import datetime, timedelta

from drf.models import Author

INVALID_CREDENTIALS_ERROR = _('Unable to login with provided credentials.')
INACTIVE_ACCOUNT_ERROR = _('User account is disabled.')
INVALID_TOKEN_ERROR = _('Invalid token for given user.')
PASSWORD_MISMATCH_ERROR = _('The two password fields didn\'t match.')
USERNAME_MISMATCH_ERROR = _('The two {0} fields didn\'t match.')
INVALID_PASSWORD_ERROR = _('Invalid password.')


try:
    from django.contrib.sites.shortcuts import get_current_site
except ImportError:
    from django.contrib.sites.models import get_current_site


def encode_uid(pk):
    try:
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        return urlsafe_base64_encode(force_bytes(pk)).decode()
    except ImportError:
        from django.utils.http import int_to_base36
        return int_to_base36(pk)


def decode_uid(pk):
    try:
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_text
        return force_text(urlsafe_base64_decode(pk))
    except ImportError:
        from django.utils.http import base36_to_int
        return base36_to_int(pk)


def send_email(to_email, from_email, context, subject_template_name,
               plain_body_template_name=None, html_body_template_name=None):
    assert plain_body_template_name or html_body_template_name
    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())

    if plain_body_template_name:
        plain_body = loader.render_to_string(plain_body_template_name, context)
        email_message = EmailMultiAlternatives(subject, plain_body, from_email, [to_email])
        if html_body_template_name:
            html_body = loader.render_to_string(html_body_template_name, context)
            email_message.attach_alternative(html_body, 'text/html')
    else:
        html_body = loader.render_to_string(html_body_template_name, context)
        email_message = EmailMessage(subject, html_body, from_email, [to_email])
        email_message.content_subtype = 'html'

    email_message.send()


class ActionViewMixin(object):

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return self.action(serializer)
        else:
            return response.Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class SendEmailViewMixin(object):
    token_generator = None
    subject_template_name = None
    plain_body_template_name = None
    html_body_template_name = None

    def send_email(self, to_email, from_email, context):
        send_email(to_email, from_email, context, **self.get_send_email_extras())

    def get_send_email_kwargs(self, user):
        return {
            'from_email': django_settings.DJOSER['DEFAULT_FROM_EMAIL'],
            'to_email': user.email,
            'context': self.get_email_context(user),
        }

    def get_send_email_extras(self):
        return {
            'subject_template_name': self.get_subject_template_name(),
            'plain_body_template_name': self.get_plain_body_template_name(),
            'html_body_template_name': self.get_html_body_template_name(),
        }

    def get_subject_template_name(self):
        return self.subject_template_name

    def get_plain_body_template_name(self):
        return self.plain_body_template_name

    def get_html_body_template_name(self):
        return self.html_body_template_name

    def get_email_context(self, user):
        token = self.token_generator.make_token(user)
        uid = encode_uid(user.pk)
        try:
            domain = django_settings.DJOSER['DOMAIN']
            site_name = django_settings.DJOSER['SITE_NAME']
        except KeyError:
            site = get_current_site(self.request)
            domain, site_name = site.domain, site.name
        return {
            'user': user,
            'domain': domain,
            'site_name': site_name,
            'uid': uid,
            'token': token,
            'protocol': 'https' if self.request.is_secure() else 'http',
        }


def jwt_payload_handler(author):
    username_field = Author.USERNAME_FIELD
    username = author.get_username()

    payload = {
        'user_id': author.pk,
        'email': author.email,
        'username': username,
        'exp': datetime.utcnow() + django_settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
    }

    payload[username_field] = username

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if django_settings.JWT_AUTH['JWT_ALLOW_REFRESH']:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )
    return payload


def jwt_get_username_from_payload_handler(payload):
    """
    Override this function if username is formatted differently in payload
    """
    return payload.get('username')


def jwt_encode_handler(payload):
    return jwt.encode(
        payload,
        django_settings.JWT_AUTH['JWT_SECRET_KEY'],
        django_settings.JWT_AUTH['JWT_ALGORITHM']
    ).decode('utf-8')


def jwt_decode_handler(token):
    options = {
        'verify_exp': django_settings.JWT_AUTH['JWT_VERIFY_EXPIRATION'],
    }

    return jwt.decode(
        token,
        django_settings.JWT_AUTH['JWT_SECRET_KEY'],
        django_settings.JWT_AUTH['JWT_VERIFY'],
        options=options,
        leeway=django_settings.JWT_AUTH['JWT_LEEWAY'],
        audience=django_settings.JWT_AUTH['JWT_AUDIENCE'],
        issuer=django_settings.JWT_AUTH['JWT_ISSUER'],
        algorithms=[django_settings.JWT_AUTH['JWT_ALGORITHM']]
    )


def jwt_response_payload_handler(token, user=None, request=None):
    """
    Returns the response data for both the login and refresh views.
    Override to return a custom response such as including the
    serialized representation of the User.
    Example:
    def jwt_response_payload_handler(token, user=None, request=None):
        return {
            'token': token,
            'user': UserSerializer(user).data
        }
    """
    return {
        'token': token
    }

