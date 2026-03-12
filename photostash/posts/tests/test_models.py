import pytest
from django.db import IntegrityError

from photostash.posts.models import Post
from photostash.posts.tests.factories import PhotoFactory, PostFactory


@pytest.mark.django_db
class TestPost:
    def test_create(self):
        obj = PostFactory()
        assert obj.pk is not None

    def test_str(self):
        obj = PostFactory()
        assert str(obj) == obj.title

    def test_get_absolute_url(self):
        obj = PostFactory()
        assert obj.get_absolute_url() == f"/posts/{obj.pk}/"


@pytest.mark.django_db
class TestPhoto:
    def test_create(self):
        obj = PhotoFactory()
        assert obj.pk is not None

    def test_str(self):
        obj = PhotoFactory()
        assert str(obj) == str(obj.photo)

    def test_unique_cover_per_post(self):
        post = PostFactory()
        PhotoFactory(post=post, is_cover=True)
        with pytest.raises(IntegrityError):
            PhotoFactory(post=post, is_cover=True)


@pytest.mark.django_db
class TestPostQuerySet:
    def test_with_cover_photo_returns_path(self):
        post = PostFactory()
        cover = PhotoFactory(post=post, is_cover=True)
        result = Post.objects.with_cover_photo().get(pk=post.pk)
        assert result.cover_photo == str(cover.photo)

    def test_with_cover_photo_returns_none_without_cover(self):
        post = PostFactory()
        PhotoFactory(post=post, is_cover=False)
        result = Post.objects.with_cover_photo().get(pk=post.pk)
        assert result.cover_photo is None
