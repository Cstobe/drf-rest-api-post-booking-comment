import jwt
from calendar import timegm
from datetime import datetime, timedelta

from django.utils import timezone
from django.contrib.auth import authenticate
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings

from rest_framework import serializers
from rest_framework.authtoken.models import Token

from drf.models import Author, Post, PostImage, BookingOption, Comment, Booking, BookingDateTime
from drf import utils

class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    posts = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='post-detail')
    bookings = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='booking-detail')
    comments = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='comment-detail')
	
    class Meta:
        model = Author
        fields = ('url', 'username', 'password', 'email', 'first_name', 'last_name', 'birthday', 'phone_number', 'date_joined', 'is_active', 'last_login', 'posts', 'bookings', 'comments')
        write_only_fields = ('password',)
        read_only_fields = ('url', 'date_joined')

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
        if not self.context['view'].token_generator.check_token(self.author, attrs['token']):
            raise serializers.ValidationError(self.error_messages['invalid_token'])
        return attrs


class JSONWebTokenSerializer(serializers.Serializer):
    """
    Serializer class used to validate a username and password.
    'username' is identified by the custom Author.USERNAME_FIELD.
    Returns a JSON Web Token that can be used to authenticate later calls.
    """
    def __init__(self, *args, **kwargs):
        """
        Dynamically add the USERNAME_FIELD to self.fields.
        """
        super(JSONWebTokenSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    @property
    def username_field(self):
        return Author.USERNAME_FIELD

    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }

        if all(credentials.values()):
            author = authenticate(**credentials)

            if author:
                if not author.is_active:
                    msg = _('Author account is not active.')
                    raise serializers.ValidationError(msg)

                payload = utils.jwt_payload_handler(author)

                return {
                    'token': utils.jwt_encode_handler(payload),
                    'user': author
                }
            else:
                msg = _('Unable to login with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)


class VerificationBaseSerializer(serializers.Serializer):
    """
    Abstract serializer used for verifying and refreshing JWTs.
    """
    token = serializers.CharField()

    def validate(self, attrs):
        msg = 'Please define a validate method.'
        raise NotImplementedError(msg)

    def _check_payload(self, token):
        # Check payload valid (based off of JSONWebTokenAuthentication,
        # may want to refactor)
        try:
            payload = utils.jwt_decode_handler(token)
        except jwt.ExpiredSignature:
            msg = _('Signature has expired.')
            raise serializers.ValidationError(msg)
        except jwt.DecodeError:
            msg = _('Error decoding signature.')
            raise serializers.ValidationError(msg)

        return payload

    def _check_user(self, payload):
        authorname = utils.jwt_get_username_from_payload_handler(payload)

        if not authorname:
            msg = _('Invalid payload.')
            raise serializers.ValidationError(msg)

        # Make sure user exists
        try:
            author = Author.objects.get(username=authorname)
        except Author.DoesNotExist:
            msg = _("Author doesn't exist.")
            raise serializers.ValidationError(msg)

        if not author.is_active:
            msg = _('Author account is not active.')
            raise serializers.ValidationError(msg)

        return author


class VerifyJSONWebTokenSerializer(VerificationBaseSerializer):
    """
    Check the veracity of an access token.
    """

    def validate(self, attrs):
        token = attrs['token']

        payload = self._check_payload(token=token)
        author = self._check_user(payload=payload)

        return {
            'token': token,
            'user': author
        }


class RefreshJSONWebTokenSerializer(VerificationBaseSerializer):
    """
    Refresh an access token.
    """

    def validate(self, attrs):
        token = attrs['token']

        payload = self._check_payload(token=token)
        author = self._check_user(payload=payload)
        # Get and check 'orig_iat'
        orig_iat = payload.get('orig_iat')

        if orig_iat:
            # Verify expiration
            refresh_limit = django_settings.JWT_AUTH['JWT_REFRESH_EXPIRATION_DELTA'] 

            if isinstance(refresh_limit, timedelta):
                refresh_limit = (refresh_limit.days * 24 * 3600 +
                                 refresh_limit.seconds)

            expiration_timestamp = orig_iat + int(refresh_limit)
            now_timestamp = timegm(datetime.utcnow().utctimetuple())

            if now_timestamp > expiration_timestamp:
                msg = _('Refresh has expired.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('orig_iat field is required.')
            raise serializers.ValidationError(msg)

        new_payload = utils.jwt_payload_handler(author)
        new_payload['orig_iat'] = orig_iat

        return {
            'token': utils.jwt_encode_handler(new_payload),
            'user': author
        }


class PostSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    parent = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')
    childs = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='post-detail')
    images = serializers.HyperlinkedRelatedField(queryset=PostImage.objects.all(), many=True, view_name='image-detail')
    bookingoptions = serializers.HyperlinkedRelatedField(queryset=BookingOption.objects.all(), many=True, view_name='bookingoption-detail')
    bookings = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='booking-detail')
    comments = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='comment-detail')

    class Meta:
        model = Post
        fields = ('url', 'author', 'parent', 'childs', 'images', 'bookingoptions', 'bookings', 'comments', 'title', 'content', 'type', 'geoid', 'created', 'updated')
	
    def create(self, validated_data):
        images = validated_data.pop('images')
        bookingoptions = validated_data.pop('bookingoptions')
        post = Post.objects.create(**validated_data)
        if images:
            for image in images:
                PostImage.objects.create(post=post, **image)
        if bookingoptions:
            for option in bookingoptions:
                BookingOption.objects.create(post=post, **option)
        return post
	
	
class PostImageSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')

    class Meta:
        model = PostImage
        fields = ('url', 'author', 'name', 'post', 'created', 'updated')
		

class BookingOptionSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')

    class Meta:
        model = BookingOption
        fields = ('url', 'author', 'post', 'type', 'value', 'unit')
		
		
class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')
    parent = serializers.HyperlinkedRelatedField(read_only=True, view_name='comment-detail')
    childs = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='comment-detail')

    class Meta:
        model = Comment
        fields = ('url', 'author', 'post', 'parent', 'childs', 'content', 'rating', 'created', 'updated')	
	
		
class BookingSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, view_name='post-detail')
    bookingoption = serializers.HyperlinkedRelatedField(read_only=True, view_name='bookingoption-detail')
    bookingdatetime = serializers.HyperlinkedRelatedField(queryset=BookingDateTime.objects.all(), view_name='bookingdatetime-detail')

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
	
	
class BookingDateTimeSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(read_only=True, view_name='author-detail')
    post = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='post-detail')

    class Meta:
        model = BookingDateTime
        fields = ('url', 'author', 'post', 'begin', 'end')


