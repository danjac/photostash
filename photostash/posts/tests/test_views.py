import base64

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from photostash.posts.models import Photo, Post
from photostash.posts.tests.factories import PhotoFactory, PostFactory

# Minimal 1×1 pixel PNG — valid image accepted by Pillow
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _make_image(name: str = "test.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _PNG_1X1, content_type="image/png")


@pytest.mark.django_db
class TestPostList:
    def test_get(self, client, auth_user):
        PostFactory.create_batch(3)
        response = client.get(reverse("posts:post_list"))
        assert response.status_code == 200

    def test_htmx_partial(self, client, auth_user):
        response = client.get(
            reverse("posts:post_list"),
            headers={"HX-Request": "true", "HX-Target": "post-list"},
        )
        assert response.status_code == 200

    def test_redirect_if_not_logged_in(self, client):
        response = client.get(reverse("posts:post_list"))
        assert response.status_code == 302


@pytest.mark.django_db
class TestPostDetail:
    def test_get(self, client, auth_user):
        obj = PostFactory()
        response = client.get(reverse("posts:post_detail", args=[obj.pk]))
        assert response.status_code == 200

    def test_get_with_photos(self, client, auth_user):
        obj = PostFactory()
        PhotoFactory(post=obj, is_cover=True)
        response = client.get(reverse("posts:post_detail", args=[obj.pk]))
        assert response.status_code == 200

    def test_404(self, client, auth_user):
        response = client.get(reverse("posts:post_detail", args=[0]))
        assert response.status_code == 404

    def test_redirect_if_not_logged_in(self, client):
        obj = PostFactory()
        response = client.get(reverse("posts:post_detail", args=[obj.pk]))
        assert response.status_code == 302


@pytest.mark.django_db
class TestPostCreate:
    def test_get(self, client, auth_user):
        response = client.get(reverse("posts:post_create"))
        assert response.status_code == 200

    def test_htmx_partial(self, client, auth_user):
        response = client.get(
            reverse("posts:post_create"),
            headers={"HX-Request": "true", "HX-Target": "post-form"},
        )
        assert response.status_code == 200

    def test_post_no_photos_returns_error(self, client, auth_user):
        response = client.post(
            reverse("posts:post_create"),
            data={"title": "Test Post", "description": "Test description"},
        )
        assert response.status_code == 200
        assert not Post.objects.filter(title="Test Post").exists()

    def test_post_valid_with_photos(self, client, auth_user):
        response = client.post(
            reverse("posts:post_create"),
            data={
                "title": "Photo Post",
                "description": "With photos",
                "photos": [_make_image("a.png"), _make_image("b.png")],
            },
        )
        assert response.status_code == 302
        post = Post.objects.get(title="Photo Post")
        assert post.photos.count() == 2
        assert post.photos.filter(is_cover=True).count() == 1

    def test_post_invalid(self, client, auth_user):
        response = client.post(reverse("posts:post_create"), data={})
        assert response.status_code == 200

    def test_redirect_if_not_logged_in(self, client):
        response = client.get(reverse("posts:post_create"))
        assert response.status_code == 302


@pytest.mark.django_db
class TestPostEdit:
    def test_get(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        response = client.get(reverse("posts:post_edit", args=[obj.pk]))
        assert response.status_code == 200

    def test_htmx_partial(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        response = client.get(
            reverse("posts:post_edit", args=[obj.pk]),
            headers={"HX-Request": "true", "HX-Target": "post-form"},
        )
        assert response.status_code == 200

    def test_post_valid(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        PhotoFactory(post=obj, is_cover=True)
        response = client.post(
            reverse("posts:post_edit", args=[obj.pk]),
            data={"title": "Updated Post", "description": "Updated description"},
        )
        assert response.status_code == 302
        assert response.url == obj.get_absolute_url()

    def test_post_no_photos_returns_error(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        response = client.post(
            reverse("posts:post_edit", args=[obj.pk]),
            data={"title": "Updated Post", "description": "Updated description"},
        )
        assert response.status_code == 200

    def test_post_valid_adds_photos(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        response = client.post(
            reverse("posts:post_edit", args=[obj.pk]),
            data={
                "title": "Updated Post",
                "description": "Updated description",
                "photos": [_make_image()],
            },
        )
        assert response.status_code == 302
        assert obj.photos.count() == 1
        assert obj.photos.filter(is_cover=True).count() == 1

    def test_post_valid_new_photo_not_cover_if_cover_exists(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        PhotoFactory(post=obj, is_cover=True)
        response = client.post(
            reverse("posts:post_edit", args=[obj.pk]),
            data={
                "title": "Updated Post",
                "description": "Updated description",
                "photos": [_make_image()],
            },
        )
        assert response.status_code == 302
        assert obj.photos.filter(is_cover=True).count() == 1

    def test_post_invalid(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        response = client.post(reverse("posts:post_edit", args=[obj.pk]), data={})
        assert response.status_code == 200

    def test_404(self, client, auth_user):
        response = client.get(reverse("posts:post_edit", args=[0]))
        assert response.status_code == 404

    def test_forbidden_if_not_owner(self, client, auth_user):
        obj = PostFactory()
        response = client.get(reverse("posts:post_edit", args=[obj.pk]))
        assert response.status_code == 403

    def test_redirect_if_not_logged_in(self, client):
        obj = PostFactory()
        response = client.get(reverse("posts:post_edit", args=[obj.pk]))
        assert response.status_code == 302


@pytest.mark.django_db
class TestPostDelete:
    def test_get(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        response = client.get(reverse("posts:post_delete", args=[obj.pk]))
        assert response.status_code == 200

    def test_delete(self, client, auth_user):
        obj = PostFactory(owner=auth_user)
        response = client.delete(reverse("posts:post_delete", args=[obj.pk]))
        assert response.status_code == 302
        assert not Post.objects.filter(pk=obj.pk).exists()

    def test_404(self, client, auth_user):
        response = client.delete(reverse("posts:post_delete", args=[0]))
        assert response.status_code == 404

    def test_forbidden_if_not_owner(self, client, auth_user):
        obj = PostFactory()
        response = client.delete(reverse("posts:post_delete", args=[obj.pk]))
        assert response.status_code == 403

    def test_redirect_if_not_logged_in(self, client):
        obj = PostFactory()
        response = client.get(reverse("posts:post_delete", args=[obj.pk]))
        assert response.status_code == 302


@pytest.mark.django_db
class TestPhotoDelete:
    def test_delete(self, client, auth_user):
        obj = PhotoFactory(post=PostFactory(owner=auth_user))
        response = client.delete(
            reverse("posts:photo_delete", args=[obj.post_id, obj.pk])
        )
        assert response.status_code == 200
        assert not Photo.objects.filter(pk=obj.pk).exists()

    def test_404(self, client, auth_user):
        post = PostFactory(owner=auth_user)
        response = client.delete(reverse("posts:photo_delete", args=[post.pk, 0]))
        assert response.status_code == 404

    def test_forbidden_if_not_owner(self, client, auth_user):
        obj = PhotoFactory()
        response = client.delete(
            reverse("posts:photo_delete", args=[obj.post_id, obj.pk])
        )
        assert response.status_code == 403

    def test_redirect_if_not_logged_in(self, client):
        obj = PhotoFactory()
        response = client.delete(
            reverse("posts:photo_delete", args=[obj.post_id, obj.pk])
        )
        assert response.status_code == 302


@pytest.mark.django_db
class TestPhotoSetCover:
    def test_post(self, client, auth_user):
        post = PostFactory(owner=auth_user)
        cover = PhotoFactory(post=post, is_cover=True)
        new = PhotoFactory(post=post, is_cover=False)
        response = client.post(reverse("posts:photo_set_cover", args=[post.pk, new.pk]))
        assert response.status_code == 200
        cover.refresh_from_db()
        new.refresh_from_db()
        assert not cover.is_cover
        assert new.is_cover

    def test_404(self, client, auth_user):
        post = PostFactory(owner=auth_user)
        response = client.post(reverse("posts:photo_set_cover", args=[post.pk, 0]))
        assert response.status_code == 404

    def test_forbidden_if_not_owner(self, client, auth_user):
        obj = PhotoFactory()
        response = client.post(
            reverse("posts:photo_set_cover", args=[obj.post_id, obj.pk])
        )
        assert response.status_code == 403

    def test_redirect_if_not_logged_in(self, client):
        obj = PhotoFactory()
        response = client.post(
            reverse("posts:photo_set_cover", args=[obj.post_id, obj.pk])
        )
        assert response.status_code == 302
