from rest_framework import serializers
from drf.models import Author, Post, PostImage, BookingOption, Comment, Booking, BookingDateTime


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    posts = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='post-detail')
    bookings = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='booking-detail')
    comments = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='comment-detail')
    followees = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='author-detail')
	
    class Meta:
        model = Author
        fields = ('url', 'username', 'password', 'email', 'first_name', 'last_name', 'birthday', 'phone_number', 'date_joined', 'is_active', 'last_login', 'posts', 'bookings', 'comments', 'followees')
        write_only_fields = ('password',)
        read_only_fields = ('url','followees','last_login', 'date_joined', 'is_active',)

	def get_gender(self,obj):
            return obj.get_gender_display()
		
    def create(self, validated_data):
        author = Author.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            date_joined=timezone.now(),
            last_login=date_joined,
            is_active=True
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


