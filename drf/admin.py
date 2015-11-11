from django.contrib import admin
from drf.models import Author, Post, PostImage, BookingOption, Comment, Booking, BookingDateTime

admin.site.register(Author)
admin.site.register(Post)
admin.site.register(PostImage)
admin.site.register(BookingOption)
admin.site.register(Comment)
admin.site.register(Booking)
admin.site.register(BookingDateTime)

