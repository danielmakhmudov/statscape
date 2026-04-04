import logging
from unittest.mock import MagicMock
from django.db.models import QuerySet
import pytest
from datetime import datetime, timezone
from core.factories import UserGameFactory
from core.services.user_data_service import (
    get_or_fetch_user_profile,
    update_user_data,
    _get_user_library_from_db,
    _fetch_steam_api_data,
    _fetch_igdb_api_data,
    _prepare_game_instances,
    _get_themes_map,
    _get_games_map,
    _join_games_and_themes,
)
from users.factories import UserFactory
from users.models import User
from core.models import Theme, Game


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


@pytest.mark.django_db
def test_update_user_data_success(mock_steam_api, monkeypatch):
    UserFactory.create(steam_id="12345", nickname="old-nickname")
    mock_steam_api.get_user_profile.return_value = {
        "steamid": "12345",
        "personaname": "new-nickname",
        "realname": "new-realname",
        "avatarfull": "new-avatar-url",
        "timecreated": 1582654560,
    }
    mock_library = MagicMock()
    monkeypatch.setattr("core.services.user_data_service.get_or_fetch_user_library", mock_library)

    result = update_user_data(steam_id="12345")
    updated_user = User.objects.get(steam_id="12345")

    assert result == updated_user
    assert updated_user.steam_id == "12345"
    assert updated_user.nickname == "new-nickname"
    assert updated_user.realname == "new-realname"
    assert updated_user.avatar_url == "new-avatar-url"
    assert updated_user.steam_user_since == datetime.fromtimestamp(1582654560, tz=timezone.utc)
    mock_steam_api.get_user_profile.assert_called_once_with("12345")
    mock_library.assert_called_once_with("12345", force_update=True)


@pytest.mark.django_db
def test_update_user_data_empty_user_profile_response(mock_steam_api):
    mock_steam_api.get_user_profile.return_value = {}

    updated_user = update_user_data("12345")

    assert updated_user is None
    mock_steam_api.get_user_profile.assert_called_once_with("12345")


@pytest.mark.django_db
def test_update_user_data_missing_user_in_db(mock_steam_api, caplog):
    mock_steam_api.get_user_profile.return_value = {"steamid": "12345"}

    with caplog.at_level(logging.WARNING):
        updated_user = update_user_data(steam_id="12345")

    assert updated_user is None
    assert "User with steam_id 12345 not found for update" in caplog.text


@pytest.mark.django_db
def test_update_user_data_missing_timecreated(mock_steam_api, monkeypatch):
    UserFactory.create(steam_id="12345")
    mock_steam_api.get_user_profile.return_value = {
        "steamid": "12345",
        "personaname": "nickname",
        "realname": "realname",
        "avatarfull": "avatar-url",
    }
    monkeypatch.setattr("core.services.user_data_service.get_or_fetch_user_library", MagicMock())

    updated_user = update_user_data(steam_id="12345")

    assert updated_user.steam_id == "12345"
    assert updated_user.steam_user_since is None


@pytest.mark.django_db
def test_get_user_library_from_db_success():
    UserFactory.create(steam_id="12345")
    user = User.objects.get(steam_id="12345")
    UserGameFactory.create_batch(3, user=user)

    user_library = _get_user_library_from_db(steam_id="12345", force_update=False)

    assert user_library.count() == 3
    assert isinstance(user_library, QuerySet)
    assert all(ul.user == user for ul in user_library)


@pytest.mark.django_db
def test_get_user_library_from_db_missing_user():
    UserGameFactory.create_batch(3)

    user_library = _get_user_library_from_db(steam_id="12345678", force_update=False)

    assert isinstance(user_library, QuerySet)
    assert user_library.count() == 0


@pytest.mark.django_db
def test_get_user_library_from_db_user_has_no_games():
    UserFactory.create(steam_id="12345")
    result = _get_user_library_from_db(steam_id="12345", force_update=False)

    assert isinstance(result, User)
    assert result.steam_id == "12345"


@pytest.mark.django_db
def test_get_user_library_from_db_force_update():
    UserFactory.create(steam_id="12345")
    user = User.objects.get(steam_id="12345")
    UserGameFactory.create_batch(3, user=user)

    result = _get_user_library_from_db(steam_id="12345", force_update=True)

    assert isinstance(result, User)
    assert result.steam_id == "12345"


@pytest.mark.django_db
def test_fetch_steam_api_data_empty_api_response(monkeypatch, mock_steam_api):
    mock_steam_api.get_user_library.return_value = {}
    user = UserFactory.create(steam_id="12345")

    api_games_map, steam_app_ids = _fetch_steam_api_data(user)

    assert (api_games_map, steam_app_ids) == ({}, [])


@pytest.mark.django_db
def test_fetch_steam_api_data_success(monkeypatch, mock_steam_api):
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

    with caplog.at_level(logging.WARNING):
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
        "100": {
            "themes": [
                {"id": 1, "name": "RPG"},
                {"id": 2, "name": "Sci-Fi"},
            ]
        },
        "200": {
            "themes": [
                {"id": 1, "name": "RPG Duplicate"},
                {"id": 3, "name": "Puzzle"},
            ]
        },
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
        "200": {
            "themes": [
                {"id": 1, "name": "RPG Duplicate"},
                {"id": 3, "name": "Adventure"},
            ]
        },
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


def test_prepare_game_instances_success():
    steam_api_games_map = {
        "100": {"name": "Game A", "img_icon_url": "logo-a"},
        "200": {"name": "Game B", "img_icon_url": "logo-b"},
    }
    igdb_data_map = {
        "100": {"rating": 92.5, "time_to_beat": 14.0},
        "200": {"rating": 77.0, "time_to_beat": 6.5},
    }

    game_instances = _prepare_game_instances(steam_api_games_map, igdb_data_map)
    games_by_app_id = {g.app_id: g for g in game_instances}

    assert len(game_instances) == 2
    assert all(isinstance(g, Game) for g in game_instances)
    assert games_by_app_id["100"].name == "Game A"
    assert (
        games_by_app_id["100"].logo_url
        == "https://media.steampowered.com/steamcommunity/public/images/apps/100/logo-a.jpg"
    )
    assert (
        games_by_app_id["100"].header_url
        == "https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg"
    )
    assert games_by_app_id["100"].rating == 92.5
    assert games_by_app_id["100"].time_to_beat == 14.0
    assert games_by_app_id["200"].name == "Game B"


def test_prepare_game_instances_partially_valid_data():
    steam_api_games_map = {
        "100": {"name": "Game A"},
        "200": {"name": None, "img_icon_url": "logo-b"},
        "300": {},
    }
    igdb_data_map = {
        "100": {"rating": 88.0},
        "200": {"time_to_beat": 9.0},
    }

    game_instances = _prepare_game_instances(steam_api_games_map, igdb_data_map)
    games_by_app_id = {g.app_id: g for g in game_instances}

    assert len(game_instances) == 3
    assert games_by_app_id["100"].rating == 88.0
    assert games_by_app_id["100"].time_to_beat == 0.0
    assert games_by_app_id["100"].logo_url is None
    assert games_by_app_id["200"].name == ""
    assert (
        games_by_app_id["200"].logo_url
        == "https://media.steampowered.com/steamcommunity/public/images/apps/200/logo-b.jpg"
    )
    assert games_by_app_id["200"].rating == 0.0
    assert games_by_app_id["200"].time_to_beat == 9.0
    assert games_by_app_id["300"].name == ""
    assert games_by_app_id["300"].rating == 0.0
    assert games_by_app_id["300"].time_to_beat == 0.0
    assert games_by_app_id["300"].logo_url is None
    assert (
        games_by_app_id["300"].header_url
        == "https://cdn.cloudflare.steamstatic.com/steam/apps/300/header.jpg"
    )


def test_prepare_game_instances_empty_game_map_returns_empty_list():
    game_instances = _prepare_game_instances({}, {"100": {"rating": 90.0}})

    assert game_instances == []


@pytest.mark.django_db
def test_get_themes_map_success_creates_and_returns_requested_themes():
    Theme.objects.create(igdb_id=999, name="Unrelated Theme")
    themes_objects = [
        Theme(igdb_id=1, name="RPG"),
        Theme(igdb_id=2, name="Adventure"),
    ]
    unique_themes = {
        1: {"id": 1, "name": "RPG"},
        2: {"id": 2, "name": "Adventure"},
    }

    themes_map = _get_themes_map(themes_objects, unique_themes)

    assert set(themes_map.keys()) == {1, 2}
    assert themes_map[1].name == "RPG"
    assert themes_map[2].name == "Adventure"
    assert Theme.objects.filter(igdb_id=1).exists() is True
    assert Theme.objects.filter(igdb_id=2).exists() is True


@pytest.mark.django_db
def test_get_themes_map_empty_input_returns_empty_map():
    themes_map = _get_themes_map([], {})

    assert themes_map == {}


@pytest.mark.django_db
def test_get_themes_map_updates_existing_theme_name():
    Theme.objects.create(igdb_id=1, name="Old Name")
    themes_objects = [Theme(igdb_id=1, name="New Name")]
    unique_themes = {1: {"id": 1, "name": "New Name"}}

    themes_map = _get_themes_map(themes_objects, unique_themes)

    assert themes_map[1].name == "New Name"
    assert Theme.objects.get(igdb_id=1).name == "New Name"


@pytest.mark.django_db
def test_get_games_map_success_creates_and_returns_requested_games():
    Game.objects.create(
        app_id="999",
        name="Unrelated Game",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/999/header.jpg",
        rating=0.0,
        time_to_beat=0.0,
    )
    game_instances = [
        Game(
            app_id="100",
            name="Game A",
            logo_url="https://example.com/logo-a.jpg",
            header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
            rating=90.0,
            time_to_beat=12.0,
        ),
        Game(
            app_id="200",
            name="Game B",
            logo_url=None,
            header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/200/header.jpg",
            rating=70.0,
            time_to_beat=6.0,
        ),
    ]
    steam_api_games_map = {"100": {"appid": 100}, "200": {"appid": 200}}

    games_map = _get_games_map(game_instances, steam_api_games_map)

    assert set(games_map.keys()) == {"100", "200"}
    assert games_map["100"].name == "Game A"
    assert games_map["200"].name == "Game B"
    assert Game.objects.filter(app_id="100").exists() is True
    assert Game.objects.filter(app_id="200").exists() is True


@pytest.mark.django_db
def test_get_games_map_empty_input_returns_empty_map():
    games_map = _get_games_map([], {})

    assert games_map == {}


@pytest.mark.django_db
def test_get_games_map_updates_existing_game_on_conflict():
    Game.objects.create(
        app_id="100",
        name="Old Name",
        logo_url="https://example.com/old-logo.jpg",
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header-old.jpg",
        rating=10.0,
        time_to_beat=2.0,
    )
    game_instances = [
        Game(
            app_id="100",
            name="New Name",
            logo_url="https://example.com/new-logo.jpg",
            header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header-new.jpg",
            rating=95.0,
            time_to_beat=15.0,
        )
    ]
    steam_api_games_map = {"100": {"appid": 100}}

    games_map = _get_games_map(game_instances, steam_api_games_map)

    updated_game = Game.objects.get(app_id="100")
    assert games_map["100"].name == "New Name"
    assert updated_game.name == "New Name"
    assert updated_game.logo_url == "https://example.com/new-logo.jpg"
    assert (
        updated_game.header_url
        == "https://cdn.cloudflare.steamstatic.com/steam/apps/100/header-new.jpg"
    )
    assert updated_game.rating == 95.0
    assert updated_game.time_to_beat == 15.0


@pytest.mark.django_db
def test_join_games_and_themes_success_creates_relations():
    game_100 = Game.objects.create(
        app_id="100",
        name="Game A",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    game_200 = Game.objects.create(
        app_id="200",
        name="Game B",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/200/header.jpg",
        rating=70.0,
        time_to_beat=6.0,
    )
    theme_1 = Theme.objects.create(igdb_id=1, name="RPG")
    theme_2 = Theme.objects.create(igdb_id=2, name="Adventure")
    games_map = {"100": game_100, "200": game_200}
    themes_map = {1: theme_1, 2: theme_2}
    igdb_data_map = {
        "100": {"themes": [{"id": 1}, {"id": 2}]},
        "200": {"themes": [{"id": 2}]},
    }

    _join_games_and_themes(games_map, igdb_data_map, themes_map)

    through = Game.themes.through.objects
    assert through.filter(game_id=game_100.id, theme_id=theme_1.id).exists() is True
    assert through.filter(game_id=game_100.id, theme_id=theme_2.id).exists() is True
    assert through.filter(game_id=game_200.id, theme_id=theme_2.id).exists() is True


@pytest.mark.django_db
def test_join_games_and_themes_skips_missing_uid_and_missing_theme_obj():
    game_100 = Game.objects.create(
        app_id="100",
        name="Game A",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    theme_1 = Theme.objects.create(igdb_id=1, name="RPG")
    games_map = {"100": game_100}
    themes_map = {1: theme_1}
    igdb_data_map = {
        "100": {"themes": [{"id": 1}, {"id": 999}]},
        "999": {"themes": [{"id": 1}]},
    }

    _join_games_and_themes(games_map, igdb_data_map, themes_map)

    through = Game.themes.through.objects
    assert through.filter(game_id=game_100.id, theme_id=theme_1.id).exists() is True
    assert through.count() == 1


@pytest.mark.django_db
def test_join_games_and_themes_empty_relations_does_not_create_anything():
    game_100 = Game.objects.create(
        app_id="100",
        name="Game A",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    unrelated_theme = Theme.objects.create(igdb_id=2, name="Adventure")
    games_map = {"100": game_100}
    themes_map = {2: unrelated_theme}
    igdb_data_map = {"100": {"themes": [{"id": 1}]}}

    _join_games_and_themes(games_map, igdb_data_map, themes_map)

    assert Game.themes.through.objects.count() == 0


@pytest.mark.django_db
def test_join_games_and_themes_ignore_conflicts_on_duplicate_relations():
    game_100 = Game.objects.create(
        app_id="100",
        name="Game A",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    theme_1 = Theme.objects.create(igdb_id=1, name="RPG")
    games_map = {"100": game_100}
    themes_map = {1: theme_1}
    igdb_data_map = {"100": {"themes": [{"id": 1}]}}

    _join_games_and_themes(games_map, igdb_data_map, themes_map)
    _join_games_and_themes(games_map, igdb_data_map, themes_map)

    assert Game.themes.through.objects.count() == 1
