import pytest
import logging
import requests
import datetime
from core.services.igdb_api_service import ConfigurationError, IGDBClient
from unittest.mock import MagicMock
from core.models import TokenStorage
from core.factories import TokenStorageFactory


def test_init_success(igdb_client):
    assert igdb_client.IGDB_CLIENT_ID == "fake-igdb_client_id"
    assert igdb_client.IGDB_CLIENT_SECRET == "fake-igdb_client_secret"


@pytest.mark.parametrize(
    "IGDB_CLIENT_ID, IGDB_CLIENT_SECRET",
    [
        (None, "fake-igdb_client_secret"),
        ("fake-igdb_client_id", None),
        (None, None),
        ("", ""),
        (" ", " "),
        (" ", "fake-igdb_client_secret"),
        ("fake-igdb_client_id", " "),
    ],
    ids=[
        "without_client_id",
        "without_client_secret",
        "client_id_and_secret_are_none",
        "client_id_and_secret_are_empty_strings",
        "client_id_and_secret_are_whitespaces",
        "client_id_is_whitespace",
        "client_secret_is_whitespace",
    ],
)
def test_init_configuration_error(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, caplog):
    with caplog.at_level(logging.ERROR):
        with pytest.raises(
            ConfigurationError, match="IGDB_CLIENT_ID and IGDB_CLIENT_SECRET are required"
        ):
            IGDBClient(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)

    assert "IGDB_CLIENT_ID or IGDB_CLIENT_SECRET isn't found" in caplog.text


@pytest.mark.django_db
def test_get_access_token_success(igdb_client, token_storage):
    access_token = igdb_client.get_access_token()

    assert access_token == token_storage.access_token


@pytest.mark.django_db
def test_get_access_token_no_token_in_db(igdb_client, mock_post, monkeypatch):
    monkeypatch.setattr("core.services.igdb_api_service.requests.post", mock_post)

    access_token = igdb_client.get_access_token()

    assert TokenStorage.objects.filter(access_token="fake-access-token").exists()
    assert access_token == "fake-access-token"
    mock_post.assert_called_once_with(
        url="https://id.twitch.tv/oauth2/token",
        params={
            "client_id": igdb_client.IGDB_CLIENT_ID,
            "client_secret": igdb_client.IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
    )


@pytest.mark.django_db
def test_get_access_token_expired(igdb_client, mock_post, expired_token_storage, monkeypatch):
    monkeypatch.setattr("core.services.igdb_api_service.requests.post", mock_post)

    access_token = igdb_client.get_access_token()

    assert access_token == "fake-access-token"
    assert TokenStorage.objects.filter(access_token="fake-access-token").exists()
    assert TokenStorage.objects.count() == 1
    mock_post.assert_called_once_with(
        url="https://id.twitch.tv/oauth2/token",
        params={
            "client_id": igdb_client.IGDB_CLIENT_ID,
            "client_secret": igdb_client.IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
    )


@pytest.mark.django_db
def test_get_access_token_expires_now(igdb_client, mock_post, monkeypatch):
    TokenStorageFactory.create(expires_at=datetime.datetime.now(datetime.timezone.utc))
    monkeypatch.setattr("core.services.igdb_api_service.requests.post", mock_post)

    access_token = igdb_client.get_access_token()

    assert access_token == "fake-access-token"
    mock_post.assert_called_once()


@pytest.mark.django_db
def test_get_access_token_bad_response(igdb_client, monkeypatch, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post = MagicMock(return_value=mock_response)
    monkeypatch.setattr("core.services.igdb_api_service.requests.post", mock_post)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception):
            igdb_client.get_access_token()

    assert "IGDB token request failed with status code: 500" in caplog.text


@pytest.mark.django_db
def test_get_access_token_request_exception(igdb_client, monkeypatch, caplog):
    mock_response = MagicMock(side_effect=requests.RequestException)

    monkeypatch.setattr("core.services.igdb_api_service.requests.post", mock_response)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(requests.RequestException):
            igdb_client.get_access_token()

    assert "Error: Failed to get IGDB ACCESS TOKEN:" in caplog.text


@pytest.mark.parametrize(
    "access_token", ["", " ", None], ids=["empty_string", "whitespace", "None"]
)
@pytest.mark.django_db
def test_get_access_token_invalid_access_token(igdb_client, access_token, monkeypatch, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": access_token,
        "expires_in": 12345,
        "token_type": "bearer",
    }
    mock_post = MagicMock(return_value=mock_response)
    monkeypatch.setattr("core.services.igdb_api_service.requests.post", mock_post)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="Invalid IGDB token payload: missing access_token"):
            igdb_client.get_access_token()

    assert "Error: invalid access_token value in IGDB response" in caplog.text


@pytest.mark.parametrize("expires_in", ["abc", None], ids=["string_value", "None"])
@pytest.mark.django_db
def test_get_access_token_invalid_expires_in_value(igdb_client, expires_in, monkeypatch, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "fake-access-token",
        "expires_in": expires_in,
        "token_type": "bearer",
    }
    mock_post = MagicMock(return_value=mock_response)
    monkeypatch.setattr("core.services.igdb_api_service.requests.post", mock_post)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="Invalid IGDB token payload: invalid expires_in"):
            igdb_client.get_access_token()

    assert "Error: invalid expires_in value in IGDB response" in caplog.text
