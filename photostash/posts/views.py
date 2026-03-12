from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods, require_safe

from photostash.http.decorators import require_form_methods
from photostash.paginator import render_paginated_response
from photostash.partials import render_partial_response
from photostash.posts.forms import PostForm
from photostash.posts.models import Post

if TYPE_CHECKING:
    from photostash.http.request import HttpRequest
    from photostash.http.response import RenderOrRedirectResponse


@require_safe
@login_required
def post_list(request: HttpRequest) -> TemplateResponse:
    """Display a paginated list of all posts."""
    return render_paginated_response(
        request,
        "posts/post_list.html",
        Post.objects.all(),
    )


@require_safe
@login_required
def post_detail(request: HttpRequest, pk: int) -> TemplateResponse:
    """Display a single post."""
    post = get_object_or_404(Post, pk=pk)
    return TemplateResponse(request, "posts/post_detail.html", {"post": post})


@login_required
@require_form_methods
def post_create(request: HttpRequest) -> RenderOrRedirectResponse:
    """Create a new post."""
    form = PostForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.owner = request.user
        post.save()
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
        post = form.save()
        messages.success(request, "Post updated.")
        return redirect(post)
    return render_partial_response(
        request,
        "posts/post_form.html",
        {"form": form, "post": post},
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
