import pytest
from datetime import datetime, timezone
from core.services.user_data_service import get_or_fetch_user_profile
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


# def test_update_user_data_success(monkeypatch):
#     mock_api_instance = MagicMock()
#     mock_api_instance.update_user_data.return_value = {}
#     monkeypatch.setattr("core.services.user_data_service.SteamAPI", mock_api_instance)
