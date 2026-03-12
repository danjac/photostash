from typing import ClassVar

from django import forms

from photostash.posts.models import Post


class PostForm(forms.ModelForm):
    """Form for creating and editing Posts."""

    class Meta:
        model = Post
        fields: ClassVar = ["title", "description"]
