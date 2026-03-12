import pytest

from photostash.posts.tests.factories import PhotoFactory, PostFactory


@pytest.fixture
def post():
    return PostFactory()


@pytest.fixture
def photo():
    return PhotoFactory()
