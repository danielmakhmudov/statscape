from unittest.mock import MagicMock

import pytest
from django.db.models import QuerySet

from core.factories import UserGameFactory
from core.models import Game, Theme, UserGame
from core.services.user_data_service import get_or_fetch_user_library
from users.factories import UserFactory


@pytest.mark.django_db
def test_get_or_fetch_user_library_success_full_pipeline():
    UserFactory.create(steam_id="12345")
    steam_api_games = {
        "100": {
            "appid": 100,
            "name": "Game A",
            "img_icon_url": "logo-a",
            "playtime_forever": 120,
            "playtime_2weeks": 20,
            "rtime_last_played": 1700000000,
        },
        "200": {
            "appid": 200,
            "name": "Game B",
            "playtime_forever": 80,
            "playtime_2weeks": 10,
            "rtime_last_played": 1700100000,
        },
    }

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "core.services.user_data_service._fetch_steam_api_data",
            MagicMock(return_value=(steam_api_games, ["100", "200"])),
        )
        mp.setattr(
            "core.services.user_data_service._fetch_igdb_api_data",
            MagicMock(
                return_value=(
                    {
                        "100": {
                            "rating": 88.0,
                            "time_to_beat": 12.0,
                            "themes": [{"id": 1, "name": "RPG"}],
                        },
                        "200": {
                            "rating": 77.0,
                            "time_to_beat": 6.0,
                            "themes": [{"id": 2, "name": "Adventure"}],
                        },
                    },
                    [Theme(igdb_id=1, name="RPG"), Theme(igdb_id=2, name="Adventure")],
                    {1: {"id": 1, "name": "RPG"}, 2: {"id": 2, "name": "Adventure"}},
                )
            ),
        )

        result = get_or_fetch_user_library("12345")

    assert isinstance(result, QuerySet)
    assert result.count() == 2
    result_by_app_id = {ug.game.app_id: ug for ug in result}
    assert set(result_by_app_id.keys()) == {"100", "200"}
    assert result_by_app_id["100"].total_playtime == 120
    assert result_by_app_id["200"].recent_playtime == 10
    assert Game.objects.filter(app_id="100").exists() is True
    assert Game.objects.filter(app_id="200").exists() is True
    assert Theme.objects.filter(igdb_id=1).exists() is True
    assert Theme.objects.filter(igdb_id=2).exists() is True
    assert Game.objects.get(app_id="100").themes.filter(igdb_id=1).exists() is True
    assert Game.objects.get(app_id="200").themes.filter(igdb_id=2).exists() is True


@pytest.mark.django_db
def test_get_or_fetch_user_library_returns_existing_library_from_db(mock_fetch_steam_api_data):
    user = UserFactory.create(steam_id="12345")
    game_b = Game.objects.create(
        app_id="200",
        name="Beta Game",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/200/header.jpg",
        rating=0.0,
        time_to_beat=0.0,
    )
    game_a = Game.objects.create(
        app_id="100",
        name="Alpha Game",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=0.0,
        time_to_beat=0.0,
    )
    UserGameFactory.create(user=user, game=game_b)
    UserGameFactory.create(user=user, game=game_a)

    result = get_or_fetch_user_library("12345")

    assert isinstance(result, QuerySet)
    assert result.count() == 2
    assert all(ug.user == user for ug in result)
    assert [ug.game.name for ug in result] == ["Alpha Game", "Beta Game"]
    mock_fetch_steam_api_data.assert_not_called()


@pytest.mark.django_db
def test_get_or_fetch_user_library_force_update_ignores_cached_library(mock_fetch_steam_api_data):
    user = UserFactory.create(steam_id="12345")
    game_100 = Game.objects.create(
        app_id="100",
        name="Old Game",
        logo_url=None,
        header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
        rating=80.0,
        time_to_beat=8.0,
    )
    UserGame.objects.create(user=user, game=game_100, total_playtime=1, recent_playtime=1)
    mock_fetch_steam_api_data.return_value = ({}, [])

    result = get_or_fetch_user_library("12345", force_update=True)

    assert isinstance(result, QuerySet)
    assert result.count() == 0
    mock_fetch_steam_api_data.assert_called_once_with(user)


@pytest.mark.django_db
def test_get_or_fetch_user_library_returns_empty_when_steam_games_map_missing(
    mock_fetch_steam_api_data, mock_fetch_igdb_api_data
):
    UserFactory.create(steam_id="12345")
    mock_fetch_steam_api_data.return_value = ({}, [])

    result = get_or_fetch_user_library("12345")

    assert isinstance(result, QuerySet)
    assert result.count() == 0
    mock_fetch_igdb_api_data.assert_not_called()


@pytest.mark.django_db
def test_get_or_fetch_user_library_returns_empty_when_game_instances_missing(
    mock_fetch_steam_api_data,
    mock_fetch_igdb_api_data,
    mock_prepare_game_instances,
    mock_get_themes_map,
):
    UserFactory.create(steam_id="12345")
    mock_fetch_steam_api_data.return_value = ({"100": {"appid": 100}}, ["100"])
    mock_fetch_igdb_api_data.return_value = ({}, [], {})
    mock_prepare_game_instances.return_value = []

    result = get_or_fetch_user_library("12345")

    assert isinstance(result, QuerySet)
    assert result.count() == 0
    mock_get_themes_map.assert_not_called()


@pytest.mark.django_db
def test_get_or_fetch_user_library_missing_user_returns_empty_queryset():
    result = get_or_fetch_user_library("does-not-exist")

    assert isinstance(result, QuerySet)
    assert result.count() == 0


@pytest.mark.django_db
def test_get_or_fetch_user_library_rolls_back_transaction_on_failure(
    mock_fetch_steam_api_data,
    mock_fetch_igdb_api_data,
    mock_prepare_game_instances,
    mock_get_themes_map,
):
    UserFactory.create(steam_id="12345")
    mock_fetch_steam_api_data.return_value = ({"100": {"appid": 100}}, ["100"])
    mock_fetch_igdb_api_data.return_value = (
        {"100": {"themes": [{"id": 1}]}},
        [],
        {1: {"id": 1, "name": "RPG"}},
    )
    mock_prepare_game_instances.return_value = [
        Game(
            app_id="100",
            name="Game A",
            logo_url=None,
            header_url="https://cdn.cloudflare.steamstatic.com/steam/apps/100/header.jpg",
            rating=80.0,
            time_to_beat=8.0,
        )
    ]

    def failing_get_themes_map(themes_objects, unique_themes):
        Theme.objects.create(igdb_id=777, name="Should Rollback")
        raise RuntimeError("transaction failed")

    mock_get_themes_map.side_effect = failing_get_themes_map

    with pytest.raises(RuntimeError, match="transaction failed"):
        get_or_fetch_user_library("12345")

    assert Theme.objects.filter(igdb_id=777).exists() is False
    assert Game.objects.filter(app_id="100").exists() is False
    assert UserGame.objects.count() == 0
