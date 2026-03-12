from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import AnonymousUser

from photostash.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from django.test import Client

    from photostash.users.models import User


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def anonymous_user() -> AnonymousUser:
    return AnonymousUser()


@pytest.fixture
def auth_user(client: Client, user: User) -> User:
    client.force_login(user)
    return user


@pytest.fixture
def staff_user(client: Client) -> User:
    user = UserFactory(is_staff=True)
    client.force_login(user)
    return user
