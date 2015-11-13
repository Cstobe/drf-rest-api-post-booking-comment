from geopy import geocoders
from django.conf import settings as django_settings

from datetime import datetime

from django.utils import timezone
from django.contrib.auth import authenticate
from django.conf import settings as django_settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.gis.geos import GEOSGeometry, Point

from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework_gis import serializers as gis_serializers
from rest_framework_recursive.fields import RecursiveField

from drf.models import Author, Post, PostImage, BookingOption, Comment, Booking, BookingDateTime, Location, BoxedLocation
from drf import utils

class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    posts = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='post-detail')
    bookings = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='booking-detail')
    comments = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='comment-detail')
	
    class Meta:
        model = Author
        fields = ('url', 'username', 'password', 'email', 'first_name', 'last_name', 'birthday', 'phone_number', 'date_joined', 'is_active', 'posts', 'bookings', 'comments')
        write_only_fields = ('password',)
        read_only_fields = ('url', 'is_active', 'date_joined')

	def get_gender(self,obj):
            return obj.get_gender_display()
		
    def create(self, validated_data):
        author = Author.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            date_joined=timezone.now(),
            last_login=timezone.now(),
            is_active=False
        )

        if validated_data.get('first_name'):
            author.first_name = validated_data['first_name']

        if validated_data.get('last_name'):
            author.last_name = validated_data['last_name']

        if validated_data.get('birthday'):
            author.birthday = validated_data['birthday']

        if validated_data.get('phone'):
            author.phone_number = validated_data['phone']

        author.set_password(validated_data['password'])
        author.save()
        return author



class UidAndTokenSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    default_error_messages = {
        'invalid_token': utils.INVALID_TOKEN_ERROR
    }

    def validate_uid(self, value):
        try:
            uid = utils.decode_uid(value)
            self.author = Author.objects.get(pk=uid)
        except (Author.DoesNotExist, ValueError, TypeError, OverflowError) as error:
            raise serializers.ValidationError(error)
        return value

    def validate(self, attrs):
        attrs = super(UidAndTokenSerializer, self).validate(attrs)
        if not default_token_generator.check_token(self.author, attrs['token']):
            raise serializers.ValidationError(self.error_messages['invalid_token'])
        return attrs


class PostImageSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')

    class Meta:
        model = PostImage
        fields = ('url', 'author', 'name', 'id', 'post', 'created', 'updated')
		

class BookingOptionSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')

    class Meta:
        model = BookingOption
        fields = ('url', 'author', 'post', 'id', 'type', 'value', 'unit')


class LocationSerializer(gis_serializers.GeoFeatureModelSerializer):
    """ location geo serializer  """
    detail = serializers.HyperlinkedIdentityField(view_name='location-detail')

    class Meta:
        model = Location
        geo_field = 'geometry'
        fields = ['name', 'address', 'detail', 'created', 'updated']

    def create(self, validated_data):
        g = geocoders.GoogleV3(django_settings.GOOGLE_API_KEY)
        try:
            res = g.geocode(validated_data['address'], exactly_one=False)
            address, (lat, lng)= res[0]
        except:
            lat=0
            lng=0

        coordinate = GEOSGeometry('POINT(%f %f)' % (lat,lng))
        location = Location.objects.create(
            name=validated_data['name'],
            address=validated_data['address'],
            geometry=coordinate
        )
        location.save()
        return location


class BoxedLocationSerializer(gis_serializers.GeoFeatureModelSerializer):
    """ location geo serializer  """
    detail = serializers.HyperlinkedIdentityField(view_name='boxedlocation-detail')

    class Meta:
        model = BoxedLocation
        geo_field = 'geometry'
        bbox_geo_field = 'bbox_geometry'
        fields = ['name', 'detail', 'created', 'updated']



class PostSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    bookings = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='booking-detail')
    bookingdatetime = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='bookingdatetime-detail')
    comments = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='comment-detail')

    images = PostImageSerializer(required=False, many=True)
    bookingoptions = BookingOptionSerializer(required=False, many=True)
    location = LocationSerializer(required=True)

    class Meta:
        model = Post
        fields = ('url', 'author', 'images', 'bookingoptions', 'location', 'bookings', 'bookingdatetime', 'comments', 'title', 'content', 'posttype', 'created', 'updated')

    def create(self, validated_data):
        imagedatas = validated_data.pop('images')
        bookingoptiondatas = validated_data.pop('bookingoptions')
        locationdata = validated_data.pop('location')
        serializer = LocationSerializer(data=locationdata)
        if serializer.is_valid():
            location = serializer.save()
            post = Post.objects.create(location=location, **validated_data)
            if imagedatas:
                for imagedata in imagedatas:
                    PostImage.objects.create(post=post, **imagedata)
            if bookingoptiondatas:
                for optiondata in bookingoptiondatas:
                    BookingOption.objects.create(post=post, **optiondata)
            return post

		
class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')
    parent = serializers.HyperlinkedRelatedField(read_only=True, view_name='comment-detail')
    children = RecursiveField(many=True, required=False, read_only=True)

    class Meta:
        model = Comment
        fields = ('url', 'author', 'post', 'parent', 'children', 'content', 'rating', 'created', 'updated')	


class BookingDateTimeSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='post-detail')

    class Meta:
        model = BookingDateTime
        fields = ('url', 'author', 'post', 'begin', 'end')

		
class BookingSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')
    bookingoption = serializers.HyperlinkedRelatedField(read_only=True, view_name='bookingoption-detail')

    bookingdatetime = BookingDateTimeSerializer(required=True, many=True)

    class Meta:
        model = Booking
        fields = ('url', 'author', 'post', 'bookingoption', 'bookingdatetime', 'note', 'created', 'updated')
	
	def create(self, validated_data):
            bookingdatetime = validated_data.pop('bookingdatetime')
            booking = Booking.objects.create(**validated_data)
            if datetime:
                for datetime in bookingdatetime:
                    BookingDateTime.objects.create(booking=booking, **datetime)
            return booking



