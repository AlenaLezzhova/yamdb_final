from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from api_yamdb.settings import DEFAULT_FROM_EMAIL
from reviews.models import Category, Genre, Review, Title, User

from .filters import TitleFilter
from .mixins import ListCreateDestroyViewSet
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsAuthorOrAdminOrModerator)
from .serializers import (CategorySerializer, CommentSerializer,
                          CheckConfirmationCodeSerializer,
                          GenreSerializer, ReviewSerializer,
                          SendCodeSerializer, TitleCreateSerializer,
                          TitleListSerializer, UserSerializer)


@api_view(['POST'])
@permission_classes((AllowAny,))
def send_confirmation_code(request):
    """Создание пользователя и отправка кода подтверждения."""
    serializer = SendCodeSerializer(data=request.data)
    username = request.data.get('username', False)
    email = request.data.get('email', False)
    if serializer.is_valid():
        if User.objects.filter(email=email).exists():
            return Response(
                f'Пользователь с почтой {email} уже существует',
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(username=username).exists():
            return Response(
                f'Пользователь {username} уже существует',
                status=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.save()
        confirmation_code = default_token_generator.make_token(user)
        mail_subject = 'Код подтверждения'
        message = f'Ваш код подтверждения: {confirmation_code}'
        send_mail(mail_subject, message, DEFAULT_FROM_EMAIL, [email])
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_jwt_token(request):
    """Получение токена."""
    serializer = CheckConfirmationCodeSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.data.get('username')
        confirmation_code = serializer.data.get('confirmation_code')
        user = get_object_or_404(User, username=username)
        if default_token_generator.check_token(user, confirmation_code):
            token = RefreshToken.for_user(user)
            return Response(
                {'token': str(token.access_token)}, status=status.HTTP_200_OK
            )
        return Response({'confirmation_code': 'Неверный код подтверждения'},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    permission_classes = (IsAdmin,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    @action(
        detail=False, methods=['get', 'patch'],
        url_path='me', permission_classes=(IsAuthenticated,)
    )
    def about_me(self, request):
        serializer = UserSerializer(request.user)
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TitleViewSet(viewsets.ModelViewSet):
    """
    Admin может изменять произведения,
    остальные могут только читать
    """
    queryset = Title.objects.all().annotate(
        rating=Avg('reviews__score')).order_by('id')
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitleFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH',):
            return TitleCreateSerializer
        return TitleListSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet отзыва."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorOrAdminOrModerator]

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet комментария к отзыву."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrAdminOrModerator]

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get("review_id"))
        return review.comments.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id, title=title_id)
        serializer.save(author=self.request.user, review=review)


class GenreViewSet(ListCreateDestroyViewSet):
    """
       Admin может изменять жанры,
       остальные могут только читать
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(ListCreateDestroyViewSet):
    """
       Admin может менять категорию,
       остальные только читать
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'
