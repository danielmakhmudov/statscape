import logging
from unittest.mock import MagicMock
from django.db.models import QuerySet
import pytest
from datetime import datetime, timezone
from core.factories import UserGameFactory
from core.services.user_data_service import (
    get_or_fetch_user_profile,
    update_user_data,
    _get_user_library_from_db,
)
from users.factories import UserFactory
from users.models import User


@pytest.mark.django_db
def test_get_or_fetch_user_profile_user_in_db(mock_steam_api):
    mock_steam_api.get_user_profile.return_value = {}

    UserFactory.create(steam_id="12345")

    user_profile = get_or_fetch_user_profile(steam_id="12345")

    assert user_profile.steam_id == "12345"
    mock_steam_api.get_user_profile.assert_not_called()


@pytest.mark.django_db
def test_get_or_fetch_user_profile_missing_user_in_db(mock_steam_api):
    mock_steam_api.get_user_profile.return_value = {
        "steamid": "12345",
        "personaname": "nickname",
        "realname": "realname",
        "avatarfull": "avatar-url",
        "timecreated": 1582654560,
    }

    user_profile = get_or_fetch_user_profile(steam_id="12345")

    profile_in_db = User.objects.filter(steam_id="12345")
    assert profile_in_db.exists() is True
    assert user_profile.steam_id == "12345"
    assert user_profile.nickname == "nickname"
    assert user_profile.realname == "realname"
    assert user_profile.avatar_url == "avatar-url"
    assert user_profile.steam_user_since == datetime.fromtimestamp(1582654560, tz=timezone.utc)
    mock_steam_api.get_user_profile.assert_called_once_with("12345")


@pytest.mark.django_db
def test_get_or_fetch_user_profile_empty_api_response(mock_steam_api):
    mock_steam_api.get_user_profile.return_value = {}

    user_profile = get_or_fetch_user_profile(steam_id="12345")
    profile_in_db = User.objects.filter(steam_id="12345")

    assert profile_in_db.exists() is False
    assert user_profile is None


@pytest.mark.django_db
def test_get_or_fetch_user_profile_api_returns_none(mock_steam_api):
    mock_steam_api.get_user_profile.return_value = None

    user_profile = get_or_fetch_user_profile(steam_id="12345")

    assert user_profile is None
    assert User.objects.filter(steam_id="12345").exists() is False


@pytest.mark.django_db
def test_get_or_fetch_user_profile_missing_timecreated(mock_steam_api):
    mock_steam_api.get_user_profile.return_value = {
        "steamid": "12345",
        "personaname": "nickname",
        "realname": "realname",
        "avatarfull": "avatar-url",
    }

    user_profile = get_or_fetch_user_profile(steam_id="12345")

    profile_in_db = User.objects.filter(steam_id="12345")

    assert profile_in_db.exists() is True
    assert user_profile.steam_id == "12345"
    assert user_profile.nickname == "nickname"
    assert user_profile.realname == "realname"
    assert user_profile.avatar_url == "avatar-url"
    assert user_profile.steam_user_since is None


@pytest.mark.django_db
def test_update_user_data_success(mock_steam_api, monkeypatch):
    UserFactory.create(steam_id="12345", nickname="old-nickname")
    mock_steam_api.get_user_profile.return_value = {
        "steamid": "12345",
        "personaname": "new-nickname",
        "realname": "new-realname",
        "avatarfull": "new-avatar-url",
        "timecreated": 1582654560,
    }
    mock_library = MagicMock()
    monkeypatch.setattr("core.services.user_data_service.get_or_fetch_user_library", mock_library)

    result = update_user_data(steam_id="12345")
    updated_user = User.objects.get(steam_id="12345")

    assert result == updated_user
    assert updated_user.steam_id == "12345"
    assert updated_user.nickname == "new-nickname"
    assert updated_user.realname == "new-realname"
    assert updated_user.avatar_url == "new-avatar-url"
    assert updated_user.steam_user_since == datetime.fromtimestamp(1582654560, tz=timezone.utc)
    mock_steam_api.get_user_profile.assert_called_once_with("12345")
    mock_library.assert_called_once_with("12345", force_update=True)


@pytest.mark.django_db
def test_update_user_data_empty_user_profile_response(mock_steam_api):
    mock_steam_api.get_user_profile.return_value = {}

    updated_user = update_user_data("12345")

    assert updated_user is None
    mock_steam_api.get_user_profile.assert_called_once_with("12345")


@pytest.mark.django_db
def test_update_user_data_missing_user_in_db(mock_steam_api, caplog):
    mock_steam_api.get_user_profile.return_value = {"steamid": "12345"}

    with caplog.at_level(logging.WARNING):
        updated_user = update_user_data(steam_id="12345")

    assert updated_user is None
    assert "User with steam_id 12345 not found for update" in caplog.text


@pytest.mark.django_db
def test_update_user_data_missing_timecreated(mock_steam_api, monkeypatch):
    UserFactory.create(steam_id="12345")
    mock_steam_api.get_user_profile.return_value = {
        "steamid": "12345",
        "personaname": "nickname",
        "realname": "realname",
        "avatarfull": "avatar-url",
    }
    monkeypatch.setattr("core.services.user_data_service.get_or_fetch_user_library", MagicMock())

    updated_user = update_user_data(steam_id="12345")

    assert updated_user.steam_id == "12345"
    assert updated_user.steam_user_since is None


@pytest.mark.django_db
def test_get_user_library_from_db_success():
    UserFactory.create(steam_id="12345")
    user = User.objects.get(steam_id="12345")
    UserGameFactory.create_batch(3, user=user)

    user_library = _get_user_library_from_db(steam_id="12345", force_update=False)

    assert user_library.count() == 3
    assert isinstance(user_library, QuerySet)
    assert all(ul.user == user for ul in user_library)


@pytest.mark.django_db
def test_get_user_library_from_db_missing_user():
    UserGameFactory.create_batch(3)

    user_library = _get_user_library_from_db(steam_id="12345678", force_update=False)

    assert isinstance(user_library, QuerySet)
    assert user_library.count() == 0


@pytest.mark.django_db
def test_get_user_library_from_db_user_has_no_games():
    UserFactory.create(steam_id="12345")
    result = _get_user_library_from_db(steam_id="12345", force_update=False)

    assert isinstance(result, User)
    assert result.steam_id == "12345"


@pytest.mark.django_db
def test_get_user_library_from_db_force_update():
    UserFactory.create(steam_id="12345")
    user = User.objects.get(steam_id="12345")
    UserGameFactory.create_batch(3, user=user)

    result = _get_user_library_from_db(steam_id="12345", force_update=True)

    assert isinstance(result, User)
    assert result.steam_id == "12345"
