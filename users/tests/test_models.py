import pytest


@pytest.mark.django_db
def test_user_str_with_nickname(user):
    assert str(user) == user.nickname


@pytest.mark.django_db
def test_user_str_without_nickname(user_without_nickname):
    assert str(user_without_nickname) == f"User {user_without_nickname.steam_id}"
