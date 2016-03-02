from geopy import geocoders
from django.db.models import Q
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

from drf.models import Author, Post, PostImage, Comment, Booking, Location, BoxedLocation
from drf.fields import HyperlinkedSorlImageField

class AuthorSerializer(serializers.ModelSerializer):
    posts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    bookings = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
	
    class Meta:
        model = Author
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'birthday', 'phone_number', 'date_joined', 'is_active', 'posts', 'bookings', 'comments')
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


class PostImageSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    post = serializers.PrimaryKeyRelatedField(read_only=True)
    thumbnail = HyperlinkedSorlImageField(
        '400x260',
        options={"crop": "center"},
        source='image',
        read_only=True
    )
    fullsize = HyperlinkedSorlImageField('1140x668', source='image', read_only=True)

    class Meta:
        model = PostImage
        fields = ('id', 'image', 'thumbnail', 'fullsize', 'author', 'post', 'created', 'updated')
		

class LocationSerializer(gis_serializers.GeoFeatureModelSerializer):
    """ location geo serializer  """
    detail = serializers.HyperlinkedIdentityField(view_name='location-detail')

    class Meta:
        model = Location
        geo_field = 'geometry'
        fields = ['address', 'detail', 'created', 'updated']

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



class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    bookings = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    images = PostImageSerializer(required=False, many=True, read_only=True)
    location = LocationSerializer(required=True)

    class Meta:
        model = Post
        fields = ('id', 'author', 'images', 'location', 'bookings', 'comments', 'title', 'content', 'price', 'capacity', 'city', 'posttype', 'created', 'updated')

    def create(self, validated_data):
        locationdata = validated_data.pop('location')
        serializer = LocationSerializer(data=locationdata)
        if serializer.is_valid():
            location = serializer.save()
            post = Post.objects.create(location=location, **validated_data)
            return post

		
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    post = serializers.PrimaryKeyRelatedField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    children = RecursiveField(many=True, required=False, read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'author', 'post', 'parent', 'children', 'content', 'rating', 'created', 'updated')	


class BookingSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Booking
        fields = ('id', 'author', 'post', 'begin', 'end', 'title', 'status', 'created', 'updated')

    def validate(self, data):
        if Booking.objects.filter( begin__lte=data['end'], end__gte=data['begin'], post__pk=self.initial_data['postid'] ).exists():
            raise serializers.ValidationError("Overlapping dates")
        return super(BookingSerializer, self).validate(data)

