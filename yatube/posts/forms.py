from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Введите какой-нибудь текст, плиииз 😥'
        )
        self.fields['group'].empty_label = (
            'Тут можно выбрать группу 🙂'
        )
        self.fields['image']

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
