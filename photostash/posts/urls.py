from typing import TYPE_CHECKING

from django.urls import path

from photostash.posts import views

if TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

app_name = "posts"
urlpatterns: list[URLPattern | URLResolver] = [
    path("", views.post_list, name="post_list"),
    path("create/", views.post_create, name="post_create"),
    path("<int:pk>/", views.post_detail, name="post_detail"),
    path("<int:pk>/edit/", views.post_edit, name="post_edit"),
    path("<int:pk>/delete/", views.post_delete, name="post_delete"),
]
