from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import datetime, timezone as dt_timezone

import pytest

from users import pipeline
from users.models import User


@pytest.fixture
def mock_steam_api_service(monkeypatch):
    mock_service = MagicMock()
    monkeypatch.setattr(pipeline, "SteamAPI", MagicMock(return_value=mock_service))
    return mock_service


@pytest.mark.django_db
def test_create_steam_user_returns_is_new_false_when_user_already_exists(
    user, mock_steam_api_service
):
    mock_get_user_profile = MagicMock()
    mock_steam_api_service.get_user_profile = mock_get_user_profile

    result = pipeline.create_steam_user(
        strategy=None,
        details={},
        backend=None,
        response=SimpleNamespace(
            identity_url="https://steamcommunity.com/openid/id/76561198000000000"
        ),
        user=user,
    )

    assert result == {"is_new": False}
    mock_get_user_profile.assert_not_called()


@pytest.mark.parametrize(
    "response",
    [
        None,
        SimpleNamespace(),
        SimpleNamespace(identity_url=""),
        SimpleNamespace(identity_url="https://steamcommunity.com/openid/id/"),
    ],
    ids=[
        "response_is_none",
        "response_without_identity_url",
        "empty_identity_url",
        "identity_url_without_steam_id",
    ],
)
def test_create_steam_user_returns_none_when_steam_id_is_missing(response, monkeypatch):
    mock_get_user_profile = MagicMock()
    mock_service = MagicMock()
    mock_service.get_user_profile = mock_get_user_profile
    mock_steam_api = MagicMock(return_value=mock_service)
    monkeypatch.setattr(pipeline, "SteamAPI", mock_steam_api)

    result = pipeline.create_steam_user(
        strategy=None,
        details={},
        backend=None,
        response=response,
        user=None,
    )

    assert result is None
    mock_get_user_profile.assert_not_called()
    mock_steam_api.assert_not_called()


@pytest.mark.django_db
def test_create_steam_user_creates_user_from_steam_profile(mock_steam_api_service):
    steam_id = "76561198000000000"
    timecreated = 1700000000

    def mock_get_user_profile(_steam_id):
        assert _steam_id == steam_id
        return {
            "personaname": "SteamNickname",
            "realname": "Steam Real Name",
            "avatarfull": "https://cdn.example.com/avatar.png",
            "timecreated": timecreated,
        }

    mock_steam_api_service.get_user_profile = mock_get_user_profile

    result = pipeline.create_steam_user(
        strategy=None,
        details={},
        backend=None,
        response=SimpleNamespace(identity_url=f"https://steamcommunity.com/openid/id/{steam_id}"),
        user=None,
    )

    assert result["is_new"] is True
    created_user = result["user"]
    assert created_user.steam_id == steam_id
    assert created_user.nickname == "SteamNickname"
    assert created_user.realname == "Steam Real Name"
    assert created_user.avatar_url == "https://cdn.example.com/avatar.png"
    assert created_user.steam_user_since == datetime.fromtimestamp(timecreated, tz=dt_timezone.utc)
    assert User.objects.filter(pk=created_user.pk).exists()


@pytest.mark.django_db
def test_create_steam_user_uses_defaults_when_profile_fields_are_missing(mock_steam_api_service):
    steam_id = "76561198000000001"
    mock_steam_api_service.get_user_profile = lambda _: {}

    result = pipeline.create_steam_user(
        strategy=None,
        details={},
        backend=None,
        response=SimpleNamespace(identity_url=f"https://steamcommunity.com/openid/id/{steam_id}"),
        user=None,
    )

    assert result["is_new"] is True
    created_user = result["user"]
    assert created_user.steam_id == steam_id
    assert created_user.nickname == ""
    assert created_user.realname is None
    assert created_user.avatar_url == ""
    assert created_user.steam_user_since is None


def test_update_steam_user_data_does_not_call_service_when_user_is_missing(monkeypatch):
    mock_update_user_data = MagicMock()
    monkeypatch.setattr(pipeline, "update_user_data", mock_update_user_data)

    result = pipeline.update_steam_user_data(
        strategy=None,
        details={},
        backend=None,
        user=None,
    )

    assert result is None
    mock_update_user_data.assert_not_called()


def test_update_steam_user_data_does_not_call_service_when_user_is_new(monkeypatch):
    mock_update_user_data = MagicMock()
    monkeypatch.setattr(pipeline, "update_user_data", mock_update_user_data)

    result = pipeline.update_steam_user_data(
        strategy=None,
        details={},
        backend=None,
        user=SimpleNamespace(steam_id="76561198000000002"),
        is_new=True,
    )

    assert result is None
    mock_update_user_data.assert_not_called()


@pytest.mark.parametrize("is_new", [False, None])
def test_update_steam_user_data_calls_service_for_existing_user(monkeypatch, is_new):
    mock_update_user_data = MagicMock()
    monkeypatch.setattr(pipeline, "update_user_data", mock_update_user_data)
    user = SimpleNamespace(steam_id="76561198000000003")

    result = pipeline.update_steam_user_data(
        strategy=None,
        details={},
        backend=None,
        user=user,
        is_new=is_new,
    )

    assert result is None
    mock_update_user_data.assert_called_once_with("76561198000000003")


def test_update_steam_user_data_calls_service_when_is_new_flag_is_absent(monkeypatch):
    mock_update_user_data = MagicMock()
    monkeypatch.setattr(pipeline, "update_user_data", mock_update_user_data)
    user = SimpleNamespace(steam_id="76561198000000004")

    result = pipeline.update_steam_user_data(
        strategy=None,
        details={},
        backend=None,
        user=user,
    )

    assert result is None
    mock_update_user_data.assert_called_once_with("76561198000000004")
