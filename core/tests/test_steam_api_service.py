import logging
import requests
import pytest
from core.services.steam_api_service import SteamAPI, ConfigurationError
from unittest.mock import Mock


def test_steam_api_init_with_api_key(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()

    assert steam_api_instance.base_url == "https://api.steampowered.com"
    assert steam_api_instance.steam_api_key == "fake-key"
    assert steam_api_instance.session.headers["User-Agent"] == "Statscape/1.0"


def test_steam_api_init_without_api_key(monkeypatch, caplog):
    monkeypatch.delenv("STEAM_API_KEY", raising=False)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ConfigurationError, match="STEAM_API_KEY is required"):
            SteamAPI()

    assert "STEAM_API_KEY not found in .env" in caplog.text


def test_get_user_profile_success(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {"players": [{"steamid": "123"}]}}

    steam_api_instance.session.get = Mock(return_value=mock_response)
    response = steam_api_instance.get_user_profile(steam_id="123")

    assert response == {"steamid": "123"}
    steam_api_instance.session.get.assert_called_once_with(
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/",
        params={"key": "fake-key", "steamids": "123", "format": "json"},
    )


def test_get_user_profile_empty_response(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {}}

    steam_api_instance.session.get = Mock(return_value=mock_response)
    response = steam_api_instance.get_user_profile(steam_id="123")

    assert response == {}


def test_get_user_profile_empty_players_list(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {"players": []}}

    steam_api_instance.session.get = Mock(return_value=mock_response)
    response = steam_api_instance.get_user_profile(steam_id="123")

    assert response == {}


def test_get_user_profile_request_exception(monkeypatch, caplog):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.RequestException()
    steam_api_instance.session.get = Mock(return_value=mock_response)

    with caplog.at_level(logging.ERROR):
        response = steam_api_instance.get_user_profile(steam_id="123")

    assert response == {}
    assert "Steam API error for user 123:" in caplog.text
