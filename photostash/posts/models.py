from typing import ClassVar

from django.conf import settings
from django.db import models
from django.db.models import OuterRef, Q, Subquery, UniqueConstraint
from django.urls import reverse
from sorl.thumbnail import ImageField


class PostQuerySet(models.QuerySet):
    """Custom QuerySet for Post model to include additional methods for querying posts."""

    def with_cover_photo(self) -> PostQuerySet:
        """Annotate each post with the file path of its cover photo."""
        return self.annotate(
            cover_photo=Subquery(
                Photo.objects.filter(post=OuterRef("pk"), is_cover=True).values(
                    "photo"
                )[:1]
            )
        )


class Post(models.Model):
    """A user-created post containing photos."""

    objects: PostQuerySet = PostQuerySet.as_manager()  # type: ignore[assignment]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Return the post title."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the URL for the post detail view."""
        return reverse("posts:post_detail", args=[self.pk])


class Photo(models.Model):
    """A photo belonging to a Post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="photos")
    photo = ImageField(upload_to="photos/")
    is_cover = models.BooleanField(default=False)

    class Meta:
        constraints: ClassVar = [
            UniqueConstraint(
                fields=["post"],
                condition=Q(is_cover=True),
                name="unique_cover_per_post",
            )
        ]

    def __str__(self) -> str:
        """Return the photo file path."""
        return str(self.photo)
