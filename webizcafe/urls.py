from drf import views
from django.contrib import admin
from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('',
    url(r'^api/v1/$', views.APIRootView.as_view(), name='root'),
    url(r'^api/v1/register/$', views.AuthorRegisterView.as_view(), name='author-create'),
    url(r'^api/v1/activate/(?P<uid>\w+)/(?P<token>[\d\w\-]+)/$', views.ActivationView.as_view(), name='author-activate'),
    url(r'^api/v1/authors/$', views.AuthorListView.as_view(), name='author-list'),
    url(r'^api/v1/me/$', views.AuthorDetailView.as_view(), name='author-detail'),
    url(r'^api/v1/me/post/$', views.AuthorPostListView.as_view(), name='authorpost-list'),
    url(r'^api/v1/me/comment/$', views.AuthorCommentListView.as_view(), name='authorcomment-list'),
    url(r'^api/v1/me/booking/$', views.AuthorBookingListView.as_view(), name='authorbooking-list'),

    url(r'^api/v1/post/$', views.PostListCreateView.as_view(), name='post-list-create'),
    url(r'^api/v1/post/(?P<pk>[0-9]+)/$', views.PostDetailView.as_view(), name='post-detail'),
    url(r'^api/v1/post/(?P<pk>[0-9]+)/image/$', views.PostImageView.as_view(), name='postimage-detail'),
    url(r'^api/v1/post/(?P<pk>[0-9]+)/comment/$', views.PostCommentListView.as_view(), name='postcomment-list'),
    url(r'^api/v1/post/(?P<pk>[0-9]+)/booking/$', views.PostBookingListView.as_view(), name='postbooking-list'),

    url(r'^api/v1/comment/$', views.CommentCreateView.as_view(), name='comment-create'),
    url(r'^api/v1/comment/(?P<pk>[0-9]+)/$', views.CommentDetailView.as_view(), name='comment-detail'),
    url(r'^api/v1/booking/$', views.BookingCreateView.as_view(), name='booking-create'),
    url(r'^api/v1/booking/search/$', views.BookingSearchView.as_view(), name='bookingsearch-list'),
    url(r'^api/v1/booking/(?P<pk>[0-9]+)/$', views.BookingDetailView.as_view(), name='booking-detail'),

    url(r'^api/v1/obtainjwt/$', 'rest_framework_jwt.views.obtain_jwt_token', name='jwt-obtain'),
    url(r'^api/v1/verifyjwt/$', 'rest_framework_jwt.views.verify_jwt_token', name='jwt-verify'),
    url(r'^api/v1/refreshjwt/$', 'rest_framework_jwt.views.refresh_jwt_token', name='jwt-refresh'),

    url(r'^api/v1/location/$', views.LocationListCreateView.as_view(), name='location-list-create'),
    url(r'^api/v1/locations/contained_in_bbox/$', views.LocationContainedInBBoxListView.as_view(), name='location-list_contained_in_bbox_filter'),
    url(r'^api/v1/locations/within_distance_of_point/$', views.LocationWithinDistanceOfPointListView.as_view(), name='location-list_within_distance_of_point_filter'),
    url(r'^api/v1/location/(?P<pk>[0-9]+)/$', views.LocationDetailView.as_view(), name='location-detail'),
    url(r'^api/v1/areas/$', views.BoxedLocationListView.as_view(), name='boxedlocation-list'),
    url(r'^api/v1/area/(?P<pk>[0-9]+)/$', views.BoxedLocationDetailView.as_view(), name='boxedlocation-detail'),

    url(r'^api/v1/admin/$', include(admin.site.urls)),
    url(r'^api/v1/docs/', include('rest_framework_swagger.urls')),
)

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'html'])

