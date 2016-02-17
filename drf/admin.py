from django.contrib import admin
from drf.models import Author, Post, PostImage, Comment, Booking

admin.site.register(Author)
admin.site.register(Post)
admin.site.register(PostImage)
admin.site.register(Comment)
admin.site.register(Booking)

