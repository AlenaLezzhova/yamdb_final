from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
from reviews.models import Category, Comment, Genre, Review, Title, User


class SendCodeSerializer(serializers.ModelSerializer):
    """Сериализатор отправки кода подтверждения."""

    class Meta:
        model = User
        fields = ('username', 'email')

    validators = [UniqueTogetherValidator(
        queryset=User.objects.all(), fields=('username', 'email')
    )
    ]

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Имя пользователя \'me\' не разрешено.'
            )
        return value


class CheckConfirmationCodeSerializer(serializers.Serializer):
    """Сериализатор проверки кода подтверждения."""
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя."""
    class Meta:
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )
        model = User


class CategorySerializer(serializers.ModelSerializer):
    """Сериализаор модели категории"""
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор модели жанров"""
    class Meta:
        model = Genre
        exclude = ('id',)


class TitleCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания Названия"""
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all(),
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug', queryset=Genre.objects.all(), many=True
    )

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description', 'genre', 'category'
        )

    def validate_year(self, value):
        current_year = timezone.now().year
        if not 0 <= value <= current_year:
            raise serializers.ValidationError(
                'Проверьте год создания произведения (должен быть нашей эры).'
            )
        return value


class TitleListSerializer(serializers.ModelSerializer):
    """Сериализатор названия для чтения"""
    rating = serializers.IntegerField(read_only=True)
    genre = GenreSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментария."""

    review = serializers.SlugRelatedField(
        slug_field='text',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор отзыва."""

    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True,
    )

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context['view'].kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if request.method == 'POST':
            if Review.objects.filter(title=title, author=author).exists():
                raise ValidationError(
                    'У вас уже есть отзыв на это произведение'
                )
        return data

    class Meta:
        model = Review
        fields = '__all__'
