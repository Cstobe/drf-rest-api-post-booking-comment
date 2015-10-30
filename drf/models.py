from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class Author(AbstractUser):
    birthday = models.DateField(blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], blank=True, max_length=17) # validators should be a list

	
class Post(models.Model):
    author = models.ForeignKey(Author, blank=False, editable=False, related_name='posts')
    parent = models.ForeignKey('self', blank=True, editable=False, related_name='childs')

    title = models.CharField(max_length=1000, default='post title')
    content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='submitted')
    type = models.CharField(max_length=20, default='office')
    geoid = models.PositiveIntegerField()
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Post, self).save(*args, **kwargs)
		
			
class PostImage(models.Model):
    author = models.ForeignKey(Author, blank=False, editable=False, related_name='images')
    post = models.ForeignKey(Post, blank=False, editable=False, related_name='images')

    name = models.CharField(max_length=100, default='post image')
    image = models.ImageField(upload_to='postimage', max_length=1000)
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField()

    def __unicode__(self):
        return self.name


    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(PostImage, self).save(*args, **kwargs)

			
class BookingOption(models.Model):
    author = models.ForeignKey(Author, blank=False, editable=False, related_name='options')
    post = models.ForeignKey(Post, blank=False, editable=False, related_name='options')

    type = models.CharField(max_length=20, default='per day limit to 100 person')
    value = models.DecimalField(max_digits=5, decimal_places=2)
    unit = models.CharField(max_length=10, default='RMB')
		

class Comment(models.Model):
    author = models.ForeignKey(Author, blank=False, editable=False, related_name='comments')
    post = models.ForeignKey(Post, blank=False, editable=False, related_name='comments')
    parent = models.ForeignKey('self', blank=True, editable=False, related_name='childs')

    content = models.TextField(blank=True, null=True)
    rating = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default='approved')
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField()

    def __unicode__(self):
        return self.content
		
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Comment, self).save(*args, **kwargs)


class Booking(models.Model):
    author = models.ForeignKey(Author, blank=False, editable=False, related_name='bookings')
    post = models.ForeignKey(Post, blank=False, editable=False, related_name='bookings')
    bookingoption = models.ForeignKey(BookingOption, blank=False, editable=False, related_name='bookings')

    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='approved')
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Booking, self).save(*args, **kwargs)


class BookingDateTime(models.Model):
    author = models.ManyToManyField(Author, blank=False, editable=False, related_name='bookingdatetime')     # used by BookingDateTimeSerializer
    post = models.ManyToManyField(Post, blank=False, editable=False, related_name='bookingdatetime')         # used by BookingDateTimeSerializer
    booking = models.ManyToManyField(Booking, blank=False, editable=False, related_name='bookingdatetime')   # used by BookingSerializer

    begin = models.DateTimeField(editable=True)
    end = models.DateTimeField(editable=True)
    status = models.CharField(max_length=20, default='approved')


