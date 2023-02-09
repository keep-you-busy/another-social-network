from django import forms

from .models import Comment, Follow, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Фотография к посту'
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Текст комментария'
        }


class FollowForm(forms.ModelForm):

    class Meta:
        model = Follow
        fields = ('user',)
