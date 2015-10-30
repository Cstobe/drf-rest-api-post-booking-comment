from django.db import models
from django.contrib.auth import user_logged_in, user_logged_out
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings as django_settings

from rest_framework import viewsets, permissions, mixins, renderers, status, response, generics, views
from rest_framework.decorators import detail_route
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from drf.models import Author, Post, PostImage, BookingOption, Comment, Booking, BookingDateTime
from drf.serializers import AuthorSerializer, PostSerializer, PostImageSerializer, BookingOptionSerializer, CommentSerializer, BookingSerializer, BookingDateTimeSerializer
from drf.serializers import UidAndTokenSerializer, JSONWebTokenSerializer, RefreshJSONWebTokenSerializer, VerifyJSONWebTokenSerializer
from drf.permissions import IsAuthorOrReadOnly
from drf import utils, signals

class AuthorRegisterViewSet(mixins.CreateModelMixin, utils.SendEmailViewMixin, viewsets.GenericViewSet):
    """
    Author registration endpoint
    Allowed request method: post
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = AuthorSerializer
    token_generator = default_token_generator
    subject_template_name = 'activation_email_subject.txt'
    plain_body_template_name = 'activation_email_body.txt'

    def perform_create(self, serializer):
        instance = serializer.save()
        signals.user_registered.send(sender=self.__class__, user=instance, request=self.request)
        self.send_email(**self.get_send_email_kwargs(instance))

    def get_email_context(self, user):
        context = super(AuthorRegisterViewSet, self).get_email_context(user)
        context['url'] = django_settings.DJOSER['ACTIVATION_URL'].format(**context)
        return context 

class ActivationView(utils.ActionViewMixin, generics.GenericAPIView):
    """
    Use this endpoint to activate user account.
    """
    serializer_class = UidAndTokenSerializer
    permission_classes = (
        permissions.AllowAny,
    )
    token_generator = default_token_generator

    def action(self, serializer):
        serializer.author.is_active = True
        serializer.author.save()
        signals.user_activated.send(
            sender=self.__class__, user=serializer.author, request=self.request)
        return Response(status=status.HTTP_200_OK)


class JSONWebTokenAPIView(views.APIView):
    """
    Base API View that various JWT interactions inherit from.
    """
    permission_classes = ()
    authentication_classes = ()

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'view': self,
        }

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        You may want to override this if you need to provide different
        serializations depending on the incoming request.
        (Eg. admins get full serialization, others get basic serialization)
        """
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method."
            % self.__class__.__name__)
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )

        if serializer.is_valid():
            user = serializer.validated_data.get('user') or request.user
            token = serializer.validated_data.get('token')
            response_data = utils.jwt_response_payload_handler(token, user, request)

            return Response(response_data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ObtainJSONWebToken(JSONWebTokenAPIView):
    """
    API View that receives a POST with a user's username and password.
    Returns a JSON Web Token that can be used for authenticated requests.
    """
    serializer_class = JSONWebTokenSerializer


class VerifyJSONWebToken(JSONWebTokenAPIView):
    """
    API View that checks the veracity of a token, returning the token if it
    is valid.
    """
    serializer_class = VerifyJSONWebTokenSerializer


class RefreshJSONWebToken(JSONWebTokenAPIView):
    """
    API View that returns a refreshed token (with new expiration) based on
    existing token
    If 'orig_iat' field (original issued-at-time) is found, will first check
    if it's within expiration window, then copy it to the new token
    """
    serializer_class = RefreshJSONWebTokenSerializer



class AuthorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Author list, as well as detail retrieve, update, and delete endpoint
    Allowed request method: get, post, put, delete
    """
    queryset = Author.objects.filter(is_active=True)
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset.filter(pk=self.request.user.pk)[0])
        self.check_object_permissions(self.request, obj)
        return obj

    def destroy(self, request, **kwargs):
        obj = self.get_object()
        if request.data.get('username'):
            if obj.username != request.data['username']:
                return Response({'detail': 'Username does not match'}, status=status.HTTP_400_BAD_REQUEST)
        obj.is_active=False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'], url_path='change-password')
    def reset_password(self, request, **kwargs):
        obj = self.get_object()
        if request.data.get('username'):
            if obj.username != request.data['username']:
                return Response({'detail': 'Username does not match'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('current_password'):
            if not obj.check_password(request.data['current_password']):
                return Response({'detail': 'Current password does not match'}, status=status.HTTP_400_BAD_REQUEST)
        obj.set_password(request.data['new_password'])
        obj.save()
        return Response({'status': 'password reset'})
   

class PostViewSet(viewsets.ModelViewSet):
    """
    Post list, create, as well as detail retrieve, update, and delete endpoint
    Allowed request method: get, post, put, delete
    Relationals: post image, booking option in create
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]

    
class AuthorPostViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    
    """


class PostImageViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Post image list, as well as detail retrieve, update, and delete endpoint
    Allowed request method: get, post, put, delete
    """
    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
    permission_classes = [IsAuthorOrReadOnly]


class BookingOptionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Booking option list, as well as detail retrieve, update, and delete endpoint
    Allowed request method: get, post, put, delete
    """
    queryset = BookingOption.objects.all()
    serializer_class = BookingOptionSerializer
    permission_classes = [IsAuthorOrReadOnly]


class CommentViewSet(viewsets.ModelViewSet):
    """
    Comment list, create, as well as detail retrieve, update, and delete endpoint
    Allowed request method: get, post, put, delete
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrReadOnly]


class BookingViewSet(viewsets.ModelViewSet):
    """
    Booking list, create, as well as detail retrieve, update, and delete endpoint
    Allowed request method: get, post, put, delete
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthorOrReadOnly]


class BookingDateTimeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Booking date time list, as well as detail retrieve, update, and delete endpoint
    Defined request method: get, post, put, delete
    """
    queryset = BookingDateTime.objects.all()
    serializer_class = BookingDateTimeSerializer
    permission_classes = [IsAuthorOrReadOnly]


