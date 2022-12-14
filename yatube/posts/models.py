from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings

User = get_user_model()


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Введите текст',
    )

    class Meta:
        abstract = True


class Group(models.Model):
    """ Модель для сообществ """
    title = models.CharField(
        verbose_name='Название группы',
        max_length=200,
        help_text='Введите название группы',
    )
    slug = models.SlugField(
        verbose_name='Связанная ссылка',
        max_length=100,
        unique=True,
        help_text='Введите адрес ссылки',
    )
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание',
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        """ При печати объекта модели Group выводится поле title """
        return f"{self.title}"


class Post(CreatedModel):
    """ Модель для постов """
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        related_name='posts',
        help_text='Выберите группу из списка',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts',
        help_text='Выберите автора из списка или создайте нового',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:settings.CHAR_LIMIT]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='comments',
        verbose_name='Комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    created = models.DateTimeField(
        verbose_name='Дата комментария',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:settings.CHAR_LIMIT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name="Автор поста"
    )

    class Meta:
        ordering = ('-author',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow')
        ]
