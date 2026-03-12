from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_safe,
)

from photostash.http.decorators import require_DELETE, require_form_methods
from photostash.paginator import render_paginated_response
from photostash.partials import render_partial_response
from photostash.posts.forms import PostForm
from photostash.posts.models import Photo, Post

if TYPE_CHECKING:
    from photostash.http.request import HttpRequest
    from photostash.http.response import RenderOrRedirectResponse

_PHOTO_REQUIRED_ERROR = _("Please upload at least one photo.")


@require_safe
@login_required
def post_list(request: HttpRequest) -> TemplateResponse:
    """Display a paginated list of all posts."""
    return render_paginated_response(
        request,
        "posts/post_list.html",
        Post.objects.with_cover_photo(),
    )


@require_safe
@login_required
def post_detail(request: HttpRequest, pk: int) -> TemplateResponse:
    """Display a single post."""
    post = get_object_or_404(Post, pk=pk)
    photos = list(post.photos.order_by("-is_cover", "pk"))
    return TemplateResponse(
        request,
        "posts/post_detail.html",
        {"post": post, "photos": photos},
    )


@login_required
@require_form_methods
def post_create(request: HttpRequest) -> RenderOrRedirectResponse:
    """Create a new post."""
    form = PostForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        photo_files = request.FILES.getlist("photos")
        if not photo_files:
            form.add_error(None, _PHOTO_REQUIRED_ERROR)
        else:
            post = form.save(commit=False)
            post.owner = request.user
            post.save()
            for i, photo_file in enumerate(photo_files):
                Photo.objects.create(post=post, photo=photo_file, is_cover=(i == 0))
            messages.success(request, "Post created.")
            return redirect(post)
    return render_partial_response(
        request,
        "posts/post_form.html",
        {"form": form},
        target="post-form",
        partial="post_form",
    )


@login_required
@require_form_methods
def post_edit(
    request: HttpRequest, pk: int
) -> RenderOrRedirectResponse | HttpResponseForbidden:
    """Edit an existing post. Only the owner may edit."""
    post = get_object_or_404(Post, pk=pk)
    if post.owner != request.user:
        return HttpResponseForbidden()
    form = PostForm(request.POST or None, instance=post)
    if request.method == "POST" and form.is_valid():
        new_photos = request.FILES.getlist("photos")
        if not new_photos and not post.photos.exists():
            form.add_error(None, _PHOTO_REQUIRED_ERROR)
        else:
            post = form.save()
            try:
                new_cover_index = int(request.POST.get("new_cover_index", -1))
            except ValueError:
                new_cover_index = -1
            if new_photos and 0 <= new_cover_index < len(new_photos):
                post.photos.filter(is_cover=True).update(is_cover=False)
                for i, photo_file in enumerate(new_photos):
                    Photo.objects.create(
                        post=post, photo=photo_file, is_cover=(i == new_cover_index)
                    )
            else:
                for i, photo_file in enumerate(new_photos):
                    has_cover = post.photos.filter(is_cover=True).exists()
                    Photo.objects.create(
                        post=post, photo=photo_file, is_cover=(not has_cover and i == 0)
                    )
            messages.success(request, "Post updated.")
            return redirect(post)
    return render_partial_response(
        request,
        "posts/post_form.html",
        {"form": form, "post": post, "photos": post.photos.order_by("-is_cover", "pk")},
        target="post-form",
        partial="post_form",
    )


@require_http_methods(["GET", "HEAD", "DELETE"])
@login_required
def post_delete(
    request: HttpRequest, pk: int
) -> RenderOrRedirectResponse | HttpResponseForbidden:
    """Delete a post. Only the owner may delete."""
    post = get_object_or_404(Post, pk=pk)
    if post.owner != request.user:
        return HttpResponseForbidden()
    if request.method == "DELETE":
        post.delete()
        messages.success(request, "Post deleted.")
        return redirect("posts:post_list")
    return TemplateResponse(
        request,
        "posts/post_confirm_delete.html",
        {"post": post},
    )


@require_DELETE
@login_required
def photo_delete(
    request: HttpRequest, post_pk: int, pk: int
) -> HttpResponse | HttpResponseForbidden:
    """Delete a photo. Only the post owner may delete."""
    photo = get_object_or_404(Photo, pk=pk, post__pk=post_pk)
    if photo.post.owner != request.user:
        return HttpResponseForbidden()
    photo.delete()
    return HttpResponse(status=200)


@require_POST
@login_required
def photo_set_cover(
    request: HttpRequest, post_pk: int, pk: int
) -> TemplateResponse | HttpResponseForbidden:
    """Set a photo as the cover for its post. Only the post owner may do this."""
    photo = get_object_or_404(Photo, pk=pk, post__pk=post_pk)
    if photo.post.owner != request.user:
        return HttpResponseForbidden()
    Photo.objects.filter(post=photo.post).update(is_cover=False)
    photo.is_cover = True
    photo.save(update_fields=["is_cover"])
    return TemplateResponse(
        request,
        "posts/post_photos.html",
        {"post": photo.post, "photos": photo.post.photos.order_by("-is_cover", "pk")},
    )
