import pytest
from users.factories import UserFactory, SuperUserFactory


@pytest.fixture
def user_without_nickname():
    return UserFactory(nickname=None)


@pytest.fixture
def superuser():
    return SuperUserFactory()


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client
