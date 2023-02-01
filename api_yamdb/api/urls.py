from django.urls import include, path
from rest_framework import routers

from .views import (send_confirmation_code, get_jwt_token, UserViewSet,
                    CommentViewSet, GenreViewSet,
                    ReviewViewSet, TitleViewSet, CategoryViewSet)

app_name = 'api'
v1 = routers.DefaultRouter()
v1.register('users', UserViewSet, basename='users')
v1.register('titles', TitleViewSet, basename='titles')
v1.register('categories', CategoryViewSet, basename='categories')
v1.register('genres', GenreViewSet, basename='genres')
v1.register(r'titles/(?P<title_id>\d+)/reviews',
            ReviewViewSet, basename='reviews')
v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet, basename='comments'
)


urlpatterns = [
    path('v1/', include(v1.urls)),
    path('v1/auth/signup/', send_confirmation_code, name='signup'),
    path('v1/auth/token/', get_jwt_token, name='login'),
]
