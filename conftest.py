import pytest
from users.factories import UserFactory


@pytest.fixture
def user():
    return UserFactory()
