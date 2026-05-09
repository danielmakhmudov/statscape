from datetime import datetime, timezone

import pytest
from django.db.models import QuerySet

from core.factories import UserGameFactory
from core.models import Game, Theme, UserGame
from core.services.user_data_service import (
    _get_games_map,
    _get_themes_map,
    _join_games_and_themes,
    _join_user_game_instances,
    _prepare_game_instances,
)
from users.factories import UserFactory


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


@pytest.mark.django_db
def test_join_user_game_instances_success_returns_only_target_user_data():
    user = UserFactory.create(steam_id="12345")
    other_user = UserFactory.create(steam_id="99999")
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
    UserGameFactory.create(user=other_user, game=game_100)
    steam_api_games_map = {
        "100": {"playtime_forever": 120, "playtime_2weeks": 20, "rtime_last_played": 1700000000},
        "200": {"playtime_forever": 80, "playtime_2weeks": 10, "rtime_last_played": 1700100000},
    }
    game_map = {"100": game_100, "200": game_200}

    result = _join_user_game_instances(user, steam_api_games_map, game_map)

    expected_last_played_100 = datetime.fromtimestamp(1700000000, tz=timezone.utc)
    expected_last_played_200 = datetime.fromtimestamp(1700100000, tz=timezone.utc)
    result_by_app_id = {ug.game.app_id: ug for ug in result}
    assert isinstance(result, QuerySet)
    assert result.count() == 2
    assert set(result_by_app_id.keys()) == {"100", "200"}
    assert [ug.game.name for ug in result] == ["Game A", "Game B"]
    assert all(ug.user == user for ug in result)
    assert result_by_app_id["100"].total_playtime == 120
    assert result_by_app_id["100"].recent_playtime == 20
    assert result_by_app_id["100"].last_played == expected_last_played_100
    assert result_by_app_id["200"].total_playtime == 80
    assert result_by_app_id["200"].recent_playtime == 10
    assert result_by_app_id["200"].last_played == expected_last_played_200
    assert UserGame.objects.filter(user=other_user).count() == 1


@pytest.mark.django_db
def test_join_user_game_instances_skips_missing_game_obj():
    user = UserFactory.create(steam_id="12345")
    game_100 = Game.objects.create(
        app_id="100",
        name="Game A",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    steam_api_games_map = {
        "100": {"playtime_forever": 10},
        "999": {"playtime_forever": 50},
    }
    game_map = {"100": game_100}

    result = _join_user_game_instances(user, steam_api_games_map, game_map)

    assert result.count() == 1
    assert result.first().game.app_id == "100"


@pytest.mark.django_db
def test_join_user_game_instances_uses_defaults_for_incomplete_data():
    user = UserFactory.create(steam_id="12345")
    game_100 = Game.objects.create(
        app_id="100",
        name="Game A",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    steam_api_games_map = {"100": {}}
    game_map = {"100": game_100}

    result = _join_user_game_instances(user, steam_api_games_map, game_map)

    user_game = result.get(game__app_id="100")
    assert user_game.total_playtime == 0
    assert user_game.recent_playtime == 0
    assert user_game.last_played is None


@pytest.mark.django_db
def test_join_user_game_instances_returns_empty_queryset_when_nothing_to_create():
    user = UserFactory.create(steam_id="12345")
    steam_api_games_map = {"999": {"playtime_forever": 50}}
    game_map = {}

    result = _join_user_game_instances(user, steam_api_games_map, game_map)

    assert isinstance(result, QuerySet)
    assert result.count() == 0


@pytest.mark.django_db
def test_join_user_game_instances_updates_existing_entry_on_conflict():
    user = UserFactory.create(steam_id="12345")
    game_100 = Game.objects.create(
        app_id="100",
        name="Game A",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    UserGame.objects.create(
        user=user,
        game=game_100,
        total_playtime=5,
        recent_playtime=1,
        last_played=None,
    )
    steam_api_games_map = {
        "100": {"playtime_forever": 99, "playtime_2weeks": 12, "rtime_last_played": 1700200000}
    }
    game_map = {"100": game_100}

    result = _join_user_game_instances(user, steam_api_games_map, game_map)

    updated = result.get(game__app_id="100")
    assert UserGame.objects.filter(user=user, game=game_100).count() == 1
    assert updated.total_playtime == 99
    assert updated.recent_playtime == 12
    assert updated.last_played == datetime.fromtimestamp(1700200000, tz=timezone.utc)
