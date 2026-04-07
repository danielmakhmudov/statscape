import pytest
import requests
from unittest.mock import Mock, MagicMock
from core.services.steam_api_service import SteamAPI
from core.factories import (
    GenreFactory,
    ThemeFactory,
    GameFactory,
    UserGameFactory,
    TokenStorageFactory,
    ExpiredTokenStorageFactory,
)
from core.services.igdb_api_service import IGDBClient


@pytest.fixture
def genre():
    return GenreFactory()


@pytest.fixture
def theme():
    return ThemeFactory()


@pytest.fixture
def game():
    return GameFactory()


@pytest.fixture
def user_game_list():
    return UserGameFactory.build_batch(5)


@pytest.fixture
def user_game():
    return UserGameFactory.build()


@pytest.fixture
def token_storage():
    return TokenStorageFactory()


@pytest.fixture
def expired_token_storage():
    return ExpiredTokenStorageFactory()


@pytest.fixture
def steam_api_instance(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    return SteamAPI()


@pytest.fixture
def mock_steam_api(monkeypatch):
    mock_instance = MagicMock()
    monkeypatch.setattr(
        "core.services.user_data_service.SteamAPI",
        MagicMock(return_value=mock_instance),
    )
    return mock_instance


@pytest.fixture
def mock_igdb_client(monkeypatch):
    mock_instance = MagicMock()
    monkeypatch.setattr(
        "core.services.user_data_service.IGDBClient",
        MagicMock(return_value=mock_instance),
    )
    return mock_instance


@pytest.fixture
def mock_fetch_steam_api_data(monkeypatch):
    mock_instance = MagicMock()
    monkeypatch.setattr("core.services.user_data_service._fetch_steam_api_data", mock_instance)
    return mock_instance


@pytest.fixture
def mock_fetch_igdb_api_data(monkeypatch):
    mock_instance = MagicMock()
    monkeypatch.setattr("core.services.user_data_service._fetch_igdb_api_data", mock_instance)
    return mock_instance


@pytest.fixture
def mock_prepare_game_instances(monkeypatch):
    mock_instance = MagicMock()
    monkeypatch.setattr("core.services.user_data_service._prepare_game_instances", mock_instance)
    return mock_instance


@pytest.fixture
def mock_get_themes_map(monkeypatch):
    mock_instance = MagicMock()
    monkeypatch.setattr("core.services.user_data_service._get_themes_map", mock_instance)
    return mock_instance


@pytest.fixture
def mock_response_success():
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_response_status_exception():
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.RequestException()
    return mock_response


@pytest.fixture
def igdb_client():
    return IGDBClient(
        IGDB_CLIENT_ID="fake-igdb_client_id", IGDB_CLIENT_SECRET="fake-igdb_client_secret"
    )


@pytest.fixture
def mock_post():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "fake-access-token",
        "expires_in": 12345,
        "token_type": "bearer",
    }
    mock_post = MagicMock(return_value=mock_response)

    return mock_post
