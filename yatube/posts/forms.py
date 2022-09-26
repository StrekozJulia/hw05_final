from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta():
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Напечатайте текст поста.')
        return data


class CommentForm(forms.ModelForm):

    class Meta():
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Напечатайте текст комментария.')
        return data
