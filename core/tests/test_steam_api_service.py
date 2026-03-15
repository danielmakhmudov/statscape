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


def test_get_user_library_success(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "response": {"game_count": 3, "games": [{"appid": 123}, {"appid": 456}, {"appid": 789}]}
    }
    steam_api_instance.session.get = Mock(return_value=mock_response)
    endpoint = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": "fake-key",
        "steamid": "123",
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json",
    }

    response = steam_api_instance.get_user_library("123")

    assert response == {"game_count": 3, "games": [{"appid": 123}, {"appid": 456}, {"appid": 789}]}
    steam_api_instance.session.get.assert_called_once_with(endpoint, params=params)


def test_get_user_library_empty_response_dictionary(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {}}
    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_user_library(steam_id="123")

    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_user_library_empty_api_response(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}
    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_user_library(steam_id="123")

    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_user_library_empty_games_list(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {"game_count": 0, "games": []}}
    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_user_library(steam_id="123")

    assert response == {"game_count": 0, "games": []}
    steam_api_instance.session.get.assert_called_once()


def test_get_user_library_without_games_list(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {"game_count": 0}}
    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_user_library(steam_id="123")

    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_user_library_raise_for_status_exception(monkeypatch, caplog):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.RequestException()
    steam_api_instance.session.get = Mock(return_value=mock_response)

    with caplog.at_level(logging.ERROR):
        response = steam_api_instance.get_user_library(steam_id="123")

    assert "Steam API error for user 123:" in caplog.text
    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_user_library_request_exception(monkeypatch, caplog):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    steam_api_instance.session.get = Mock(side_effect=requests.RequestException("network error"))

    with caplog.at_level(logging.ERROR):
        response = steam_api_instance.get_user_library(steam_id="123")

    assert "Steam API error for user 123:" in caplog.text
    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_recently_played_games_success(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "response": {
            "total_count": 6,
            "games": [
                {"appid": 111},
                {"appid": 222},
                {"appid": 333},
                {"appid": 444},
                {"appid": 555},
            ],
        }
    }
    steam_api_instance.session.get = Mock(return_value=mock_response)
    endpoint = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
    params = {
        "steamid": "123",
        "key": "fake-key",
        "count": 5,
        "format": "json",
    }
    response = steam_api_instance.get_recently_played_games(steam_id="123")

    assert response == {
        "total_count": 6,
        "games": [
            {"appid": 111},
            {"appid": 222},
            {"appid": 333},
            {"appid": 444},
            {"appid": 555},
        ],
    }
    steam_api_instance.session.get.assert_called_once_with(endpoint, params=params)


def test_get_recently_played_games_empty_api_response(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}

    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_recently_played_games(steam_id="123")

    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_recently_played_games_empty_response_dictionary(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {}}

    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_recently_played_games(steam_id="123")

    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_recently_played_games_empty_games_list(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {"total_count": 0, "games": []}}

    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_recently_played_games(steam_id="123")

    assert response == {"total_count": 0, "games": []}
    steam_api_instance.session.get.assert_called_once()


def test_get_recently_played_games_without_games_list(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": {"total_count": 0}}
    steam_api_instance.session.get = Mock(return_value=mock_response)

    response = steam_api_instance.get_recently_played_games(steam_id="123")

    assert response == {}
    steam_api_instance.session.get.assert_called_once()


def test_get_recently_played_games_request_exception(monkeypatch, caplog):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    steam_api_instance.session.get = Mock(side_effect=requests.RequestException())

    with caplog.at_level(logging.ERROR):
        response = steam_api_instance.get_recently_played_games(steam_id="123")

    assert response == {}
    assert "Steam API error for user 123:" in caplog.text
    steam_api_instance.session.get.assert_called_once()


def test_get_recently_played_games_raise_for_status_exception(monkeypatch, caplog):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.RequestException()
    steam_api_instance.session.get = Mock(return_value=mock_response)

    with caplog.at_level(logging.ERROR):
        response = steam_api_instance.get_recently_played_games(steam_id="123")

    assert response == {}
    assert "Steam API error for user 123:" in caplog.text
    steam_api_instance.session.get.assert_called_once()
