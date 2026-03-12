from typing import ClassVar

from django.contrib import admin

from photostash.posts.models import Photo, Post


class PhotoInline(admin.TabularInline):
    """Inline admin for Photos within a Post."""

    model = Photo
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post model admin."""

    list_display: ClassVar = ["title", "owner", "created"]
    search_fields: ClassVar = ["title", "description"]
    list_filter: ClassVar = ["created"]
    inlines: ClassVar = [PhotoInline]
