from drf import views
from django.contrib import admin
from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('',
    url(r'^$', views.APIRootView.as_view(), name='root'),
    url(r'^register/$', views.AuthorRegisterView.as_view(), name='author-create'),
    url(r'^activate/(?P<uid>\w+)/(?P<token>[\d\w\-]+)/$', views.ActivationView.as_view(), name='author-activate'),
    url(r'^authors/$', views.AuthorListView.as_view(), name='author-list'),
    url(r'^author/(?P<pk>[0-9]+)/$', views.AuthorDetailView.as_view(), name='author-detail'),
    url(r'^post/$', views.PostListCreateView.as_view(), name='post-list-create'),
    url(r'^post/(?P<pk>[0-9]+)/$', views.PostDetailView.as_view(), name='post-detail'),
    url(r'^image/(?P<pk>[0-9]+)/$', views.PostImageDetailView.as_view(), name='image-detail'),
    url(r'^bookingoption/(?P<pk>[0-9]+)/$', views.BookingOptionDetailView.as_view, name='bookingoption-detail'),
    url(r'^comment/$', views.CommentCreateView.as_view(), name='comment-create'),
    url(r'^comment/(?P<pk>[0-9]+)/$', views.CommentDetailView.as_view(), name='comment-detail'),
    url(r'^booking/$', views.BookingCreateView.as_view(), name='booking-create'),
    url(r'^booking/(?P<pk>[0-9]+)/$', views.BookingDetailView.as_view(), name='booking-detail'),
    url(r'^bookingdatetime/(?P<pk>[0-9]+)/$', views.BookingDateTimeDetailView.as_view(), name='bookingdatatime-detail'),

    url(r'^obtainjwt/$', 'rest_framework_jwt.views.obtain_jwt_token', name='jwt-obtain'),
    url(r'^verifyjwt/$', 'rest_framework_jwt.views.verify_jwt_token', name='jwt-verify'),
    url(r'^refreshjwt/$', 'rest_framework_jwt.views.refresh_jwt_token', name='jwt-refresh'),

    url(r'^location/$', views.LocationListCreateView.as_view(), name='location-list-create'),
    url(r'^locations/contained_in_bbox/$', views.LocationContainedInBBoxListView.as_view(), name='location-list_contained_in_bbox_filter'),
    url(r'^locations/within_distance_of_point/$', views.LocationWithinDistanceOfPointListView.as_view(), name='location-list_within_distance_of_point_filter'),
    url(r'^location/(?P<pk>[0-9]+)/$', views.LocationDetailView.as_view(), name='location-detail'),
    url(r'^areas/$', views.BoxedLocationListView.as_view(), name='boxedlocation-list'),
    url(r'^area/(?P<pk>[0-9]+)/$', views.BoxedLocationDetailView.as_view(), name='boxedlocation-detail'),

    url(r'^admin/$', include(admin.site.urls)),
    url(r'^docs/$', include('rest_framework_swagger.urls')),
)

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'html'])

