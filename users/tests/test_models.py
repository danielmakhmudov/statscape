import pytest
from users.factories import UserFactory


@pytest.mark.django_db
def test_user_str_with_nickname(user):
    assert str(user) == user.nickname


@pytest.mark.django_db
def test_user_str_without_nickname(user_without_nickname):
    assert str(user_without_nickname) == f"User {user_without_nickname.steam_id}"


@pytest.mark.django_db
def test_create_user_without_steam_id():
    with pytest.raises(ValueError):
        UserFactory(steam_id=None)


@pytest.mark.django_db
def test_create_superuser(superuser):
    assert superuser.is_superuser is True
    assert superuser.is_staff is True
