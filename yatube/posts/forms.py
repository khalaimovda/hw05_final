from django.forms import ModelForm, Textarea

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")

        labels = {
            "text": "Текст",
            "group": "Группа",
            "image": "Изображение",
        }

        widgets = {
            "text": Textarea(attrs={"rows": 10, "style": "width:100%"})
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)

        labels = {
            "text": "Текст",
        }

        widgets = {
            "text": Textarea(attrs={"rows": 7, "style": "width:100%"})
        }
