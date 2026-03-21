import pytest
import requests
from unittest.mock import Mock
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
