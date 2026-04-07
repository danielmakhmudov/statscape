import pytest

from core.models import Theme
from core.services.user_data_service import _fetch_igdb_api_data, _fetch_steam_api_data
from users.factories import UserFactory


@pytest.mark.django_db
def test_fetch_steam_api_data_empty_api_response(mock_steam_api):
    mock_steam_api.get_user_library.return_value = {}
    user = UserFactory.create(steam_id="12345")

    api_games_map, steam_app_ids = _fetch_steam_api_data(user)

    assert (api_games_map, steam_app_ids) == ({}, [])


@pytest.mark.django_db
def test_fetch_steam_api_data_success(mock_steam_api):
    mock_steam_api.get_user_library.return_value = {
        "games": [
            {"appid": 100, "name": "Game A"},
            {"appid": 200, "name": "Game B"},
            {"appid": 300, "name": "Game C"},
        ]
    }
    user = UserFactory.create(steam_id="12345")

    api_games_map, steam_app_ids = _fetch_steam_api_data(user)

    assert steam_app_ids == ["100", "200", "300"]
    assert api_games_map == {
        "100": {"appid": 100, "name": "Game A"},
        "200": {"appid": 200, "name": "Game B"},
        "300": {"appid": 300, "name": "Game C"},
    }
    mock_steam_api.get_user_library.assert_called_once_with(steam_id="12345")


@pytest.mark.django_db
def test_fetch_steam_api_data_without_games_key(mock_steam_api):
    mock_steam_api.get_user_library.return_value = {"response": {"game_count": 3}}
    user = UserFactory.create(steam_id="12345")

    api_games_map, steam_app_ids = _fetch_steam_api_data(user)

    assert (api_games_map, steam_app_ids) == ({}, [])


@pytest.mark.django_db
def test_fetch_steam_api_data_skips_games_without_appid(mock_steam_api, caplog):
    mock_steam_api.get_user_library.return_value = {
        "games": [
            {"name": "No Id Game"},
            {"appid": 200, "name": "Valid Game"},
            {"appid": None, "name": "Also Invalid"},
        ]
    }
    user = UserFactory.create(steam_id="12345")

    with caplog.at_level("WARNING"):
        api_games_map, steam_app_ids = _fetch_steam_api_data(user)

    assert steam_app_ids == ["200"]
    assert api_games_map == {"200": {"appid": 200, "name": "Valid Game"}}
    assert "Skipped game without appid: No Id Game" in caplog.text
    assert "Skipped game without appid: Also Invalid" in caplog.text


@pytest.mark.django_db
def test_fetch_steam_api_data_all_invalid_games_returns_empty(mock_steam_api):
    mock_steam_api.get_user_library.return_value = {
        "games": [
            {"name": "Missing AppId"},
            {"appid": None, "name": "None AppId"},
            {},
        ]
    }
    user = UserFactory.create(steam_id="12345")

    api_games_map, steam_app_ids = _fetch_steam_api_data(user)

    assert (api_games_map, steam_app_ids) == ({}, [])


@pytest.mark.django_db
def test_fetch_steam_api_data_non_dict_response_returns_empty(mock_steam_api):
    mock_steam_api.get_user_library.return_value = None
    user = UserFactory.create(steam_id="12345")

    api_games_map, steam_app_ids = _fetch_steam_api_data(user)

    assert (api_games_map, steam_app_ids) == ({}, [])


@pytest.mark.django_db
def test_fetch_igdb_api_data_success(mock_igdb_client):
    mock_igdb_client.get_igdb_data.return_value = {
        "100": {"themes": [{"id": 1, "name": "RPG"}, {"id": 2, "name": "Sci-Fi"}]},
        "200": {"themes": [{"id": 1, "name": "RPG Duplicate"}, {"id": 3, "name": "Puzzle"}]},
    }

    igdb_data_map, themes_objects, unique_themes = _fetch_igdb_api_data(["100", "200"])

    assert igdb_data_map == mock_igdb_client.get_igdb_data.return_value
    assert set(unique_themes.keys()) == {1, 2, 3}
    assert unique_themes[1]["name"] == "RPG Duplicate"
    assert isinstance(themes_objects[0], Theme)
    assert {(t.igdb_id, t.name) for t in themes_objects} == {
        (1, "RPG Duplicate"),
        (2, "Sci-Fi"),
        (3, "Puzzle"),
    }
    mock_igdb_client.get_igdb_data.assert_called_once_with(["100", "200"])


@pytest.mark.django_db
def test_fetch_igdb_api_data_invalid_api_response(mock_igdb_client):
    mock_igdb_client.get_igdb_data.return_value = []

    igdb_data_map, themes_objects, unique_themes = _fetch_igdb_api_data(["100"])

    assert igdb_data_map == {}
    assert themes_objects == []
    assert unique_themes == {}


@pytest.mark.django_db
def test_fetch_igdb_api_data_partially_valid_themes(mock_igdb_client):
    mock_igdb_client.get_igdb_data.return_value = {
        "100": {
            "themes": [
                {"id": 1, "name": "RPG"},
                {"id": None, "name": "Missing Id"},
                {"id": 2},
                {"name": "Missing Id Field"},
                {},
            ]
        },
        "200": {"themes": [{"id": 1, "name": "RPG Duplicate"}, {"id": 3, "name": "Adventure"}]},
    }

    igdb_data_map, themes_objects, unique_themes = _fetch_igdb_api_data(["100", "200"])

    assert igdb_data_map == mock_igdb_client.get_igdb_data.return_value
    assert set(unique_themes.keys()) == {1, 3}
    assert unique_themes[1]["name"] == "RPG Duplicate"
    assert {(t.igdb_id, t.name) for t in themes_objects} == {
        (1, "RPG Duplicate"),
        (3, "Adventure"),
    }


@pytest.mark.django_db
def test_fetch_igdb_api_data_empty_dict_response(mock_igdb_client):
    mock_igdb_client.get_igdb_data.return_value = {}

    igdb_data_map, themes_objects, unique_themes = _fetch_igdb_api_data(["100"])

    assert igdb_data_map == {}
    assert themes_objects == []
    assert unique_themes == {}
