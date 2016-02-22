import django_filters
from django.db import models
from django.db.models import Q
from django.conf import settings as django_settings
from django.contrib.auth.tokens import default_token_generator

from rest_framework import permissions, mixins, renderers, status, response, generics, views, filters, pagination
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser
from rest_framework.filters import DjangoFilterBackend
from rest_framework_gis.filters import *
from rest_framework_gis.pagination import GeoJsonPagination

from drf.models import Author, Post, PostImage, Comment, Booking, Location, BoxedLocation
from drf.serializers import AuthorSerializer, PostSerializer, PostImageSerializer, CommentSerializer, BookingSerializer
from drf.serializers import LocationSerializer, BoxedLocationSerializer
from drf.permissions import IsAuthorOrReadOnly

class APIRootView(views.APIView):
    """
    api root endpoint
    request method: Get
    """
    def get(self, request, format=None):
        data = {
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


class AuthorListView(generics.ListAPIView):
    """
    List all of active users
    Allowed request method: Get
    authentication is required
    """
    queryset = Author.objects.filter(is_active=True)
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]


class AuthorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete author, as well as reset password endpoint
    Allowed request method: Get, Post, Delete
    """
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        queryset = Author.objects.filter(is_active=True)
        obj = queryset.filter(pk=self.request.user.pk)[0]
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
   

class ListFilter(django_filters.CharFilter):
    def sanitize(self, value_list):
        return [v for v in value_list if v != u'']

    def customize(self, value):
        return value

    def filter(self, qs, value):
        multiple_vals = value.split(u",")
        multiple_vals = self.sanitize(multiple_vals)
        multiple_vals = map(self.customize, multiple_vals)
        actual_filter = django_filters.fields.Lookup(multiple_vals, 'in')
        return super(ListFilter, self).filter(qs, actual_filter)


class PostFilter(django_filters.FilterSet):
    posttype = ListFilter(name="posttype")
    city = ListFilter(name="city")
    min_price  = django_filters.NumberFilter(name="price", lookup_type='gte')
    max_price  = django_filters.NumberFilter(name="price", lookup_type='lte')
    min_capacity  = django_filters.NumberFilter(name="capacity", lookup_type='gte')
    max_capacity  = django_filters.NumberFilter(name="capacity", lookup_type='lte')
    min_rating = django_filters.NumberFilter(name="comments__rating", lookup_type='gte')
    latest_updated = django_filters.DateTimeFilter(name="updated", lookup_type="gte")
    class Meta:
        model = Post
        fields = ['posttype', 'city', 'min_price', 'max_price', 'min_capacity', 'max_capacity', 'min_rating', 'latest_updated']


class PostListCreateView(generics.ListCreateAPIView):
    """
    List and Create post endpoint
    Allowed request method: Get (list), Post (create)
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter,)
    filter_class = PostFilter
    search_fields= ('title', 'content', 'comment__content')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class AuthorPostListView(generics.ListAPIView):
    """
    List and Create post endpoint
    Allowed request method: Get (list)
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LargeResultsSetPagination
    def get_queryset(self):
        user = self.request.user
        return Post.objects.filter(author=user).order_by('-updated')


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete post endpoint
    Allowed request method: Get, Post, Delete
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]

    
class PostImageView(generics.CreateAPIView):
    """
    List and Create post image endpoint
    Allowed request method: Get, Post
    """
    serializer_class = PostImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (FormParser, MultiPartParser, FileUploadParser,)

    def perform_create(self, serializer):
        if 'file' in self.request.data:
            file_obj = self.request.data['file']
            post = Post.objects.get(pk=self.kwargs['pk'])
            serializer.save(author=self.request.user, post=post, image=file_obj)
            return response.Response("image has been successfully uploaded", status=status.HTTP_201_CREATED)
        else:
            return response.Response("no upload file in request data", status=status.HTTP_400_BAD_REQUEST)


class CommentCreateView(generics.CreateAPIView):
    """
    Create comment endpoint
    Allowed request method: Post
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated,]

    def perform_create(self, serializer):
        postid = self.request.data['postid']
        post = Post.objects.get(pk=postid)
        if 'parentid' in self.request.data:
            parentid = self.request.data['parentid']
            if parentid > 0:
                parent = Comment.objects.get(pk=parentid)
                return serializer.save(author=self.request.user, post=post, parent=parent)
        return serializer.save(author=self.request.user, post=post)


class PostCommentListView(generics.ListAPIView):
    """
    List Post Comment endpoint
    Allowed request method: Get
    """
    serializer_class = CommentSerializer
    permission_classes = (permissions.AllowAny,)
    def get_queryset(self):
        return Comment.objects.filter(post__pk=self.kwargs['pk'], parent=None)


class AuthorCommentListView(generics.ListAPIView):
    """
    List Post Booking endpoint
    Allowed request method: Get
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LargeResultsSetPagination
    def get_queryset(self):
        user = self.request.user
        return Comment.objects.filter(author=user).order_by('-updated')


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
    permission_classes = [permissions.IsAuthenticated,]

    def perform_create(self, serializer):
        postid = self.request.data['postid']
        post = Post.objects.get(pk=postid)
        return serializer.save(author=self.request.user, post=post)


class PostBookingListView(generics.ListAPIView):
    """
    List Post Booking endpoint
    Allowed request method: Get
    """
    serializer_class = BookingSerializer
    permission_classes = (permissions.AllowAny,)
    def get_queryset(self):
        return Booking.objects.filter(post__pk=self.kwargs['pk'])


class AuthorBookingListView(generics.ListAPIView):
    """
    List Post Booking endpoint
    Allowed request method: Get
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LargeResultsSetPagination
    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(author=user).order_by('-updated')


class BookingSearchView(generics.ListAPIView):
    """
    booking datetime list endpoint
    request method: Get (to list all booking datetime)
    search field: timefrom and timeto
    """
    serializer_class = BookingSerializer

    def get_queryset(self):
        queryset = Booking.objects.all()
        timefrom = self.request.query_params.get('from', None)
        timeto = self.request.query_params.get('to', None)
        if timefrom is not None and timeto is not None:
            queryset = queryset.filter( Q(end__lte=timefrom) | Q(begin_gte=timeto) )
        return queryset


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, and Delete booking endpoint
    Allowed request method: Get, Post, Delete
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
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


