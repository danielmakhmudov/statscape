import pytest
import logging
import requests
import datetime
import json
from core.services.igdb_api_service import ConfigurationError, IGDBAPIError, IGDBClient
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
        with pytest.raises(IGDBAPIError, match="Failed to get IGDB token"):
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


def test_get_igdb_game_ids_success():
    json_igdb_data = [
        {"id": 1200554, "game": {"id": 28856, "name": "The Crew 2"}, "uid": "646910"},
        {"id": 2614616, "game": {"id": 132181, "name": "Resident Evil 4"}, "uid": "2050650"},
    ]

    igdb_game_ids = IGDBClient.get_igdb_game_ids(json_igdb_data)

    assert igdb_game_ids == {28856, 132181}


def test_get_igdb_game_ids_duplicates():
    json_igdb_data = [
        {"id": 1200554, "game": {"id": 28856, "name": "The Crew 2"}, "uid": "646910"},
        {"id": 2614616, "game": {"id": 132181, "name": "Resident Evil 4"}, "uid": "2050650"},
        {"id": 2614616, "game": {"id": 132181, "name": "Resident Evil 4"}, "uid": "2050650"},
    ]

    igdb_game_ids = IGDBClient.get_igdb_game_ids(json_igdb_data)

    assert igdb_game_ids == {28856, 132181}


def test_get_igdb_game_ids_skips_invalid_entries():
    json_igdb_data = [
        {"id": 1200554, "game": {"id": 28856, "name": "The Crew 2"}, "uid": "646910"},
        {"id": 2614616, "game": {"id": 132181, "name": "Resident Evil 4"}},
    ]

    igdb_game_ids = IGDBClient.get_igdb_game_ids(json_igdb_data)

    assert igdb_game_ids == {28856}


@pytest.mark.parametrize(
    "json_igdb_data",
    [
        [{"id": 1200554, "game": {"name": "The Crew 2"}, "uid": "646910"}],
        [{"id": 1200554, "game": {"id": 28856, "name": "The Crew 2"}}],
        [],
        [{}],
    ],
    ids=["no_id", "no_uid", "empty_api_response", "empty_api_dictionary"],
)
def test_get_igdb_game_ids_invalid_igdb_data(json_igdb_data):
    igdb_game_ids = IGDBClient.get_igdb_game_ids(json_igdb_data)

    assert igdb_game_ids == set()


def test_get_time_to_beat_map_success():
    time_to_beat_data = [
        {"id": 71, "game_id": 231, "normally": 43503},
        {"id": 1747, "game_id": 132181, "normally": 60566},
    ]

    time_to_beat_map = IGDBClient.get_time_to_beat_map(time_to_beat_data)

    assert time_to_beat_map == {
        "231": {"id": 71, "game_id": 231, "normally": 43503},
        "132181": {"id": 1747, "game_id": 132181, "normally": 60566},
    }


def test_get_time_to_beat_map_skips_invalid_entries():
    time_to_beat_data = [
        {"id": 71, "game_id": 231, "normally": 43503},
        {"id": 1747, "normally": 60566},
    ]

    time_to_beat_map = IGDBClient.get_time_to_beat_map(time_to_beat_data)

    assert time_to_beat_map == {
        "231": {"id": 71, "game_id": 231, "normally": 43503},
    }


@pytest.mark.parametrize(
    "time_to_beat_data, expected",
    [
        ([{"id": 71, "normally": 43503}], {}),
        ([{"id": 71, "game_id": 231}], {"231": {"id": 71, "game_id": 231}}),
        ([], {}),
        ([{}], {}),
    ],
    ids=["no_game_id", "no_playtime", "empty_api_response", "empty_api_dictionary"],
)
def test_get_time_to_beat_map_invalid_api_response(time_to_beat_data, expected):
    time_to_beat_map = IGDBClient.get_time_to_beat_map(time_to_beat_data)

    assert time_to_beat_map == expected


def test_get_merged_igdb_data_mixed_data():
    json_igdb_data = [
        {"game": {"id": 231, "name": "The Crew 2"}, "uid": "646910"},
        {"game": {"id": 132181, "name": "Resident Evil 4"}, "uid": "2050650"},
        {"game": {"id": 12345, "name": "Game 3"}, "uid": "00000"},
    ]
    time_to_beat_map = {
        "231": {"id": 71, "game_id": 231, "normally": 3600},
        "132181": {"id": 1747, "game_id": 132181, "normally": 5400},
    }

    merged_data = IGDBClient.get_merged_igdb_data(json_igdb_data, time_to_beat_map)

    assert merged_data == {
        "646910": {"id": 231, "name": "The Crew 2", "time_to_beat": 1.0},
        "2050650": {"id": 132181, "name": "Resident Evil 4", "time_to_beat": 1.5},
        "00000": {"id": 12345, "name": "Game 3", "time_to_beat": 0.0},
    }


@pytest.mark.parametrize(
    "json_igdb_data",
    [
        [{"game": {}, "uid": "646910"}],
        [{"uid": "646910"}],
        [{"game": {"id": 231, "name": "The Crew 2"}}],
        [],
    ],
    ids=["empty_game_dict", "no_game_dict", "no_uid", "empty_igdb_data"],
)
def test_get_merged_igdb_data_invalid_game_data(json_igdb_data):
    time_to_beat_map = {
        "231": {"id": 71, "game_id": 231, "normally": 3600},
    }
    merged_data = IGDBClient.get_merged_igdb_data(json_igdb_data, time_to_beat_map)

    assert merged_data == {}


def test_get_merged_igdb_data_no_match():
    json_igdb_data = [{"game": {"id": 231, "name": "The Crew 2"}, "uid": "646910"}]
    time_to_beat_map = {
        "100": {"id": 71, "game_id": 100, "normally": 3600},
    }

    merged_data = IGDBClient.get_merged_igdb_data(json_igdb_data, time_to_beat_map)

    assert merged_data == {
        "646910": {"id": 231, "name": "The Crew 2", "time_to_beat": 0.0},
    }


def test_get_igdb_data_success(monkeypatch, igdb_client):
    steam_app_ids = ["646910", "2050650"]

    game_info = [
        {
            "id": 1200554,
            "game": {
                "id": 28856,
                "name": "The Crew 2",
            },
            "uid": "646910",
        },
        {
            "id": 2614616,
            "game": {
                "id": 132181,
                "name": "Resident Evil 4",
            },
            "uid": "2050650",
        },
    ]
    playtime_info = [
        {"id": 6829, "game_id": 28856, "normally": 7200},
        {"id": 1747, "game_id": 132181, "normally": 3600},
    ]
    mock_game_response = MagicMock(return_value=game_info)
    mock_playtime_response = MagicMock(return_value=playtime_info)

    monkeypatch.setattr(
        "core.services.igdb_api_service.IGDBClient.get_access_token",
        MagicMock(return_value="fake-token"),
    )
    monkeypatch.setattr("core.services.igdb_api_service.IGDBWrapper", MagicMock())

    monkeypatch.setattr(
        "core.services.igdb_api_service.IGDBClient._get_igdb_basic_game_data", mock_game_response
    )
    monkeypatch.setattr(
        "core.services.igdb_api_service.IGDBClient._get_igdb_time_to_beat_data",
        mock_playtime_response,
    )

    igdb_data = igdb_client.get_igdb_data(steam_app_ids)

    assert igdb_data == {
        "646910": {"id": 28856, "name": "The Crew 2", "time_to_beat": 2.0},
        "2050650": {"id": 132181, "name": "Resident Evil 4", "time_to_beat": 1.0},
    }


@pytest.mark.parametrize("steam_app_ids", [[], None], ids=["empty_list", "None_value"])
def test_get_igdb_data_invalid_steam_ids(igdb_client, steam_app_ids):
    igdb_data = igdb_client.get_igdb_data(steam_app_ids)

    assert igdb_data == {}


def test_get_igdb_basic_game_data_success_multiple_chunks(igdb_client):
    steam_app_ids = [str(i) for i in range(501)]
    first_chunk_payload = [{"uid": "1", "game": {"id": 11, "name": "Game 1"}}]
    second_chunk_payload = [{"uid": "2", "game": {"id": 22, "name": "Game 2"}}]
    wrapper = MagicMock()
    wrapper.api_request = MagicMock(
        side_effect=[
            json.dumps(first_chunk_payload).encode("utf-8"),
            json.dumps(second_chunk_payload).encode("utf-8"),
        ]
    )

    result = igdb_client._get_igdb_basic_game_data(steam_app_ids, wrapper)

    assert result == first_chunk_payload + second_chunk_payload
    assert wrapper.api_request.call_count == 2
    first_call_args = wrapper.api_request.call_args_list[0].args
    second_call_args = wrapper.api_request.call_args_list[1].args
    assert first_call_args[0] == "external_games"
    assert second_call_args[0] == "external_games"
    assert 'uid = ("0","1"' in first_call_args[1]
    assert 'uid = ("500")' in second_call_args[1]


def test_get_igdb_time_to_beat_data_success_multiple_chunks(igdb_client):
    igdb_game_ids = set(range(501))
    first_chunk_payload = [{"game_id": 1, "normally": 3600}]
    second_chunk_payload = [{"game_id": 500, "normally": 1800}]
    wrapper = MagicMock()
    wrapper.api_request = MagicMock(
        side_effect=[
            json.dumps(first_chunk_payload).encode("utf-8"),
            json.dumps(second_chunk_payload).encode("utf-8"),
        ]
    )

    result = igdb_client._get_igdb_time_to_beat_data(igdb_game_ids, wrapper)

    assert result == first_chunk_payload + second_chunk_payload
    assert wrapper.api_request.call_count == 2
    first_call_args = wrapper.api_request.call_args_list[0].args
    second_call_args = wrapper.api_request.call_args_list[1].args
    assert first_call_args[0] == "game_time_to_beats"
    assert second_call_args[0] == "game_time_to_beats"
    assert "game_id = (" in first_call_args[1]
    assert "game_id = (" in second_call_args[1]
