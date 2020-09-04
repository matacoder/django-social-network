from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):  # extending ModelForm, not Form as before
    class Meta:
        model = Post
        fields = ["text", "group", "image"]
        help_texts = {
            "text": "Напишите этот пост. Давайте же.",
            "group": "Стоит указать, где этот пост будет жить",
            "image": "Загрузите картинку"
        }
        labels = {
            "text": "Текст вашего поста",
            "group": "Выберите группу",
            "image": "Выберите изображение для поста"
        }


class CommentForm(ModelForm):  # extending ModelForm, not Form as before
    class Meta:
        model = Comment
        fields = ["text"]
        help_texts = {
            "text": "Напишите комментарий"
        }
        labels = {
            "text": "Текст вашего комментария"
        }
