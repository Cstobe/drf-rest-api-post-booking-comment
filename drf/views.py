from django.db import models
from django.conf import settings as django_settings
from django.contrib.auth.tokens import default_token_generator

from rest_framework import permissions, mixins, renderers, status, response, generics, views
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.filters import DjangoFilterBackend
from rest_framework_gis.filters import *
from rest_framework_gis.pagination import GeoJsonPagination

from drf.models import Author, Post, PostImage, BookingOption, Comment, Booking, BookingDateTime, Location, BoxedLocation
from drf.serializers import AuthorSerializer, PostSerializer, PostImageSerializer, BookingOptionSerializer, CommentSerializer, BookingSerializer, BookingDateTimeSerializer
from drf.serializers import UidAndTokenSerializer
from drf.serializers import LocationSerializer, BoxedLocationSerializer
from drf.permissions import IsAuthorOrReadOnly
from drf import utils, signals

class APIRootView(views.APIView):
    """
    api root endpoint
    request method: Get
    """
    def get(self, request, format=None):
        data = {
            'register': reverse('author-create', request=request, format=format),
            'authors': reverse('author-list', request=request, format=format),
            'post': reverse('post-list-create', request=request, format=format),
            'comment': reverse('comment-create', request=request, format=format),
            'booking': reverse('booking-create', request=request, format=format),
 
            'obtainjwt': reverse('jwt-obtain', request=request, format=format),
            'verifyjwt': reverse('jwt-verify', request=request, format=format),
            'refreshjwt': reverse('jwt-refresh', request=request, format=format),

            'location': reverse('location-list-create', request=request, format=format),
        }
        return Response(data)



class AuthorRegisterView(utils.SendEmailViewMixin, generics.CreateAPIView):
    """
    Author registration endpoint
    Allowed request method: Post
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
        context = super(AuthorRegisterView, self).get_email_context(user)
        context['url'] = django_settings.DJOSER['ACTIVATION_URL'].format(**context)
        return context 

class ActivationView(views.APIView):
    """
    Use this endpoint to activate user account.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, uid, token, format=None):
        dictionary = {}
        dictionary['uid'] = uid
        dictionary['token'] = token
        serializer = UidAndTokenSerializer(data=dictionary)
        if serializer.is_valid():
            serializer.author.is_active = True
            serializer.author.save()
            signals.user_activated.send(sender=self.__class__, user=serializer.author, request=self.request)
            return Response(data=uid, status=status.HTTP_200_OK)
        else:
            return response.Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class AuthorListView(generics.ListAPIView):
    """
    List all of active users
    Allowed request method: Get
    authentication is required
    """
    queryset = Author.objects.filter(is_active=True)
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AuthorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete author, as well as reset password endpoint
    Allowed request method: Get, Post, Delete
    """
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        queryset = Author.objects.filter(is_active=True)
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
   

class PostListCreateView(generics.ListCreateAPIView):
    """
    List and Create post endpoint
    Allowed request method: Get (list), Post (create)
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (permissions.AllowAny,)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete post endpoint
    Allowed request method: Get, Post, Delete
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    

class PostImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete post image endpoint
    Allowed request method: Get, Post, Delete
    """
    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
    permission_classes = [IsAuthorOrReadOnly]


class BookingOptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete booking option endpoint
    Allowed request method: Get, Post, Delete
    """
    queryset = BookingOption.objects.all()
    serializer_class = BookingOptionSerializer
    permission_classes = [IsAuthorOrReadOnly]


class CommentCreateView(generics.CreateAPIView):
    """
    Create comment endpoint
    Allowed request method: Post
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny,]


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete comment endpoint
    Allowed request method: Get, Post, Delete
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrReadOnly]


class BookingCreateView(generics.CreateAPIView):
    """
    Create booking endpoint
    Allowed request method: Post
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.AllowAny,]


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete booking endpoint
    Allowed request method: Get, Post, Delete
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthorOrReadOnly]


class BookingDateTimeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete booking date time endpoint
    Defined request method: Get, Post, Delete
    """
    queryset = BookingDateTime.objects.all()
    serializer_class = BookingDateTimeSerializer
    permission_classes = [IsAuthorOrReadOnly]



####### geodjango gis ###########
class LocationListCreateView(generics.ListCreateAPIView):
    model = Location
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
    pagination_class = GeoJsonPagination


class LocationContainedInBBoxListView(generics.ListAPIView):
    model = Location
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
    bbox_filter_field = 'geometry'
    filter_backends = (InBBoxFilter,)


class LocationWithinDistanceOfPointListView(generics.ListAPIView):
    model = Location
    serializer_class = LocationSerializer
    distance_filter_convert_meters = True
    queryset = Location.objects.all()
    distance_filter_field = 'geometry'
    filter_backends = (DistanceToPointFilter,)


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    model = Location
    serializer_class = LocationSerializer
    queryset = Location.objects.all()


class BoxedLocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    model = BoxedLocation
    serializer_class = BoxedLocationSerializer
    queryset = BoxedLocation.objects.all()


class BoxedLocationListView(generics.ListCreateAPIView):
    model = BoxedLocation
    serializer_class = BoxedLocationSerializer
    queryset = BoxedLocation.objects.all()


