from django import forms

from .models import Comment, Follow, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'group': 'Группа',
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, в которой будет относиться пост',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {"text": "Текст комментария", }
        help_texts = {"text": "Введите текст Вашего комментария.", }


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        labels = {'user': 'Подписчик', 'author': 'Автор', }
        fields = ('user', )
