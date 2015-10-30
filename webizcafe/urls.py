from drf import views
from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'register', views.AuthorRegisterViewSet, base_name="register")
router.register(r'author', views.AuthorViewSet)
router.register(r'post', views.PostViewSet)
router.register(r'image', views.PostImageViewSet)
router.register(r'bookingoption', views.BookingOptionViewSet)
router.register(r'comment', views.CommentViewSet)
router.register(r'booking', views.BookingViewSet)
router.register(r'bookingdatetime', views.BookingDateTimeViewSet)

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^activate/', views.ActivationView.as_view(), name='activate'),
    (r'^jwt-login/$', views.ObtainJSONWebToken.as_view()),
    (r'^jwt-refresh/$', views.RefreshJSONWebToken.as_view()),
    (r'^jwt-verify/$', views.VerifyJSONWebToken.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)

