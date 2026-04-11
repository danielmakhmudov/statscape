from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from users import pipeline
from users.models import User


@pytest.mark.django_db
def test_create_steam_user_returns_is_new_false_when_user_already_exists(user, monkeypatch):
    mock_get_user_profile = MagicMock()
    monkeypatch.setattr(pipeline.steam_api_service, "get_user_profile", mock_get_user_profile)

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
    monkeypatch.setattr(pipeline.steam_api_service, "get_user_profile", mock_get_user_profile)

    result = pipeline.create_steam_user(
        strategy=None,
        details={},
        backend=None,
        response=response,
        user=None,
    )

    assert result is None
    mock_get_user_profile.assert_not_called()


@pytest.mark.django_db
def test_create_steam_user_creates_user_from_steam_profile(monkeypatch):
    steam_id = "76561198000000000"

    def mock_get_user_profile(_steam_id):
        assert _steam_id == steam_id
        return {
            "personaname": "SteamNickname",
            "avatarfull": "https://cdn.example.com/avatar.png",
        }

    monkeypatch.setattr(pipeline.steam_api_service, "get_user_profile", mock_get_user_profile)

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
    assert created_user.avatar_url == "https://cdn.example.com/avatar.png"
    assert User.objects.filter(pk=created_user.pk).exists()


@pytest.mark.django_db
def test_create_steam_user_uses_defaults_when_profile_fields_are_missing(monkeypatch):
    steam_id = "76561198000000001"
    monkeypatch.setattr(pipeline.steam_api_service, "get_user_profile", lambda _: {})

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
    assert created_user.avatar_url == ""
