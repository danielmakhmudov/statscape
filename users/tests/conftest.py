import pytest
from users.factories import UserFactory, SuperUserFactory


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_without_nickname():
    return UserFactory(nickname=None)


@pytest.fixture
def superuser():
    return SuperUserFactory()
