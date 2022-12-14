from django.db import models


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    pub_date = models.DateTimeField(
        verbose_name='Дата',
        auto_now_add=True,
        db_index=True
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Введите текст',
    )

    class Meta:
        abstract = True
