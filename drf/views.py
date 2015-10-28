from django.db import models
from rest_framework import viewsets, permissions, mixins, renderers
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from drf.models import Author, Post, PostImage, BookingOption, Comment, Booking, BookingDateTime
from drf.serializers import AuthorSerializer, PostSerializer, PostImageSerializer, BookingOptionSerializer, CommentSerializer, BookingSerializer, BookingDateTimeSerializer
from drf.permissions import IsAuthorOrReadOnly

class AuthorRegisterViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """
    Author registration endpoint
    Allowed request method: post
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = AuthorSerializer


class AuthorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Author list, as well as detail retrieve, update, and delete endpoint
    Allowed request method: get, post, put, delete
    """
    queryset = Author.objects.filter(is_active=True)
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
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


