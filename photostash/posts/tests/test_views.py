import pytest
from django.urls import reverse

from photostash.posts.models import Post
from photostash.posts.tests.factories import PostFactory


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

    def test_post_valid(self, client, auth_user):
        response = client.post(
            reverse("posts:post_create"),
            data={"title": "Test Post", "description": "Test description"},
        )
        assert response.status_code == 302
        post = Post.objects.get(title="Test Post", owner=auth_user)
        assert response.url == post.get_absolute_url()

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
        response = client.post(
            reverse("posts:post_edit", args=[obj.pk]),
            data={"title": "Updated Post", "description": "Updated description"},
        )
        assert response.status_code == 302
        assert response.url == obj.get_absolute_url()

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
