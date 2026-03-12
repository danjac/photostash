import factory
from factory.django import DjangoModelFactory, ImageField

from photostash.posts.models import Photo, Post
from photostash.users.tests.factories import UserFactory


class PostFactory(DjangoModelFactory):
    class Meta:
        model = Post

    owner = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence", nb_words=5)
    description = factory.Faker("paragraph")


class PhotoFactory(DjangoModelFactory):
    class Meta:
        model = Photo

    post = factory.SubFactory(PostFactory)
    photo = ImageField()
    is_cover = False
