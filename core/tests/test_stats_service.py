import datetime as dt
import pytest
from core.models import UserGame
from django.db.models import QuerySet

from core.services.stats_service import (
    enrich_games_with_stats,
    get_chart_data,
    get_favorite_games,
    get_prepared_recently_played_games,
    get_not_played_games,
    get_potentially_not_completed_games,
)
from core.factories import UserGameFactory


def test_enrich_games_with_stats_basic():
    user_games = UserGameFactory.build_batch(10, total_playtime=60, recent_playtime=60)

    enriched_games, total_hours = enrich_games_with_stats(user_games)

    assert len(enriched_games) == len(user_games)
    assert total_hours == 10
    assert sum(g.playtime_percentage for g in enriched_games) == pytest.approx(100, abs=0.1)
    assert enriched_games[0].playtime_hours == 1
    assert enriched_games[0].recent_playtime_hours == 1


def test_enrich_games_with_stats_empty_list():
    enriched_games, total_hours = enrich_games_with_stats([])

    assert total_hours == 0.0
    assert enriched_games == []


def test_enrich_games_with_stats_sorted():
    user_game_list = [
        UserGameFactory.build(total_playtime=240),
        UserGameFactory.build(total_playtime=60),
        UserGameFactory.build(total_playtime=180),
    ]

    enriched_games, _ = enrich_games_with_stats(user_game_list)
    playtimes = [game.total_playtime for game in enriched_games]

    assert playtimes == [240, 180, 60]


def test_enrich_games_with_stats_without_playtime():
    user_game_list = UserGameFactory.build_batch(2, total_playtime=0, recent_playtime=0)

    enriched_games, _ = enrich_games_with_stats(user_game_list)

    assert enriched_games[0].playtime_percentage == 0
    assert enriched_games[1].playtime_percentage == 0


def test_enrich_games_with_stats_single_game(user_game):
    enriched_games, _ = enrich_games_with_stats([user_game])

    assert enriched_games[0].playtime_percentage == 100


def test_enrich_games_with_stats_round():
    user_game_list = [UserGameFactory.build(total_playtime=100, recent_playtime=100)]

    enriched_games, total_hours = enrich_games_with_stats(user_game_list)

    assert enriched_games[0].playtime_hours == 1.7
    assert enriched_games[0].recent_playtime_hours == 1.7
    assert total_hours == 1.7


def test_get_chart_data_basic():
    user_games = UserGameFactory.build_batch(20, total_playtime=60)
    enriched_games, total_hours = enrich_games_with_stats(user_games)

    chart_labels, chart_values, chart_hours = get_chart_data(enriched_games)

    assert len(chart_labels) == len(chart_values) == len(chart_hours) == 11
    assert chart_labels[-1] == "Others"
    assert sum(chart_values) == pytest.approx(100, abs=0.1)
    assert sum(chart_hours) == total_hours


def test_get_chart_data_only_top_games():
    user_games = UserGameFactory.build_batch(10, total_playtime=60)
    enriched_games, _ = enrich_games_with_stats(user_games)

    chart_labels, chart_values, chart_hours = get_chart_data(enriched_games)

    assert len(chart_labels) == len(chart_values) == len(chart_hours) == 10
    assert "Others" not in chart_labels


def test_get_chart_data_more_than_10_but_others_zero_percent():
    user_games = UserGameFactory.build_batch(
        10, recent_playtime=60, total_playtime=60
    ) + UserGameFactory.build_batch(5, recent_playtime=0, total_playtime=0)
    enriched_games, _ = enrich_games_with_stats(user_games)

    chart_labels, chart_values, chart_hours = get_chart_data(enriched_games)

    assert len(chart_labels) == len(chart_values) == len(chart_hours) == 10
    assert "Others" not in chart_labels


def test_get_chart_data_empty_list():
    chart_labels, chart_values, chart_hours = get_chart_data([])

    assert chart_labels == []
    assert chart_values == []
    assert chart_hours == []


def test_get_favorite_games_basic():
    user_games = UserGameFactory.build_batch(
        5, total_playtime=120, recent_playtime=120
    ) + UserGameFactory.build_batch(5, total_playtime=60, recent_playtime=60)
    enriched_games, _ = enrich_games_with_stats(user_games)

    favorite_games = get_favorite_games(enriched_games)

    assert len(favorite_games) == 5
    assert all(g.total_playtime == 120 for g in favorite_games)


def test_get_favorite_games_empty_list():
    favorite_games = get_favorite_games([])

    assert favorite_games == []


def test_get_favorite_games_three_games():
    user_games = UserGameFactory.build_batch(3, total_playtime=120, recent_playtime=120)
    enriched_games, _ = enrich_games_with_stats(user_games)

    favorite_games = get_favorite_games(enriched_games)

    assert len(favorite_games) == 3
    assert all(g.total_playtime == 120 for g in favorite_games)


def test_get_prepared_recently_played_games_basic():
    old = dt.datetime.fromtimestamp(1680723278, tz=dt.timezone.utc)  # 2023
    recent = dt.datetime.fromtimestamp(1712345678, tz=dt.timezone.utc)  # 2024
    user_games = UserGameFactory.build_batch(10, last_played=old) + UserGameFactory.build_batch(
        10, last_played=recent
    )

    recent_games = get_prepared_recently_played_games(user_games)

    assert len(recent_games) == 5
    assert all(g.last_played == recent for g in recent_games)


def test_get_prepared_recently_played_games_all_none():
    user_games = UserGameFactory.build_batch(3, last_played=None)

    recent_games = get_prepared_recently_played_games(user_games)

    assert recent_games == []


def test_get_prepared_recently_played_games_some_none():
    date = dt.datetime.fromtimestamp(1680723278, tz=dt.timezone.utc)
    user_games = UserGameFactory.build_batch(5, last_played=None) + UserGameFactory.build_batch(
        3, last_played=date
    )

    recent_games = get_prepared_recently_played_games(user_games)

    assert len(recent_games) == 3
    assert all(g.last_played == date for g in recent_games)


def test_get_prepared_recently_played_games_empty():
    user_games = get_prepared_recently_played_games([])

    assert user_games == []


@pytest.mark.django_db
def test_get_not_played_games_queryset(user):
    UserGameFactory.create_batch(5, user=user, total_playtime=0)
    UserGameFactory.create_batch(10, user=user, total_playtime=120)
    user_games = UserGame.objects.filter(user=user)
    not_played_games, games_count = get_not_played_games(user_games)

    assert games_count == not_played_games.count() == 5
    assert isinstance(not_played_games, QuerySet)
    assert all(g.total_playtime == 0 for g in not_played_games)


def test_get_not_played_games_list():
    user_games = UserGameFactory.build_batch(5, total_playtime=0) + UserGameFactory.build_batch(
        10, total_playtime=120
    )

    not_played_games, games_count = get_not_played_games(user_games)

    assert games_count == len(not_played_games) == 5
    assert isinstance(not_played_games, list)
    assert all(g.total_playtime == 0 for g in not_played_games)


def test_get_not_played_games_limit_list():
    user_games = UserGameFactory.build_batch(5, total_playtime=0)

    not_played_games, games_count = get_not_played_games(user_games, limit=2)

    assert isinstance(not_played_games, list)
    assert len(not_played_games) == 2
    assert games_count == 5


@pytest.mark.django_db
def test_get_not_played_games_limit_queryset(user):
    UserGameFactory.create_batch(5, user=user, total_playtime=0)
    user_games = UserGame.objects.filter(user=user)

    not_played_games, games_count = get_not_played_games(user_games, limit=2)

    assert isinstance(not_played_games, QuerySet)
    assert not_played_games.count() == 2
    assert games_count == 5


@pytest.mark.django_db
def test_get_not_played_games_empty_queryset(user):
    user_games = UserGame.objects.filter(user=user)
    not_played_games = get_not_played_games(user_games)

    assert isinstance(not_played_games, QuerySet)
    assert not_played_games.count() == 0


def test_get_not_played_games_empty_list():
    not_played_games = get_not_played_games([])

    assert not_played_games == []


@pytest.mark.django_db
def test_get_potentially_not_completed_games_queryset(user):
    UserGameFactory.create_batch(10, user=user, total_playtime=1000)
    UserGameFactory.create_batch(5, user=user, total_playtime=120)
    UserGameFactory.create_batch(15, user=user, total_playtime=0)

    user_games = UserGame.objects.filter(user=user)

    not_completed_games, games_count = get_potentially_not_completed_games(user_games)

    assert not_completed_games.count() == games_count == 5
    assert isinstance(not_completed_games, QuerySet)
    assert all(g.total_playtime == 120 for g in not_completed_games)


def test_get_potentially_not_completed_games_list():
    user_games = (
        UserGameFactory.build_batch(10, total_playtime=1000)
        + UserGameFactory.build_batch(5, total_playtime=120)
        + UserGameFactory.build_batch(15, total_playtime=0)
    )

    not_completed_games, games_count = get_potentially_not_completed_games(user_games)

    assert isinstance(not_completed_games, list)
    assert games_count == len(not_completed_games) == 5
    assert all(g.total_playtime == 120 for g in not_completed_games)


def test_get_potentially_not_completed_games_boundary_values():
    user_games = (
        UserGameFactory.build_batch(10, total_playtime=0)
        + UserGameFactory.build_batch(5, total_playtime=1)
        + UserGameFactory.build_batch(15, total_playtime=600)
        + UserGameFactory.build_batch(20, total_playtime=601)
    )

    not_completed_games, _ = get_potentially_not_completed_games(user_games)

    assert all(0 < g.total_playtime <= 600 for g in not_completed_games)


def test_get_potentially_not_completed_games_empty_list():
    not_completed_games = get_potentially_not_completed_games([])

    assert not_completed_games == []


@pytest.mark.django_db
def test_get_potentially_not_completed_games_empty_queryset(user):
    user_games = UserGame.objects.filter(user=user)

    not_completed_games = get_potentially_not_completed_games(user_games)

    assert isinstance(not_completed_games, QuerySet)
    assert not_completed_games.count() == 0


@pytest.mark.django_db
def test_get_potentially_not_completed_games_limit_queryset(user):
    UserGameFactory.create_batch(5, user=user, total_playtime=120)
    user_games = UserGame.objects.filter(user=user)

    not_completed_games, games_count = get_potentially_not_completed_games(user_games, limit=2)

    assert isinstance(not_completed_games, QuerySet)
    assert not_completed_games.count() == 2
    assert games_count == 5


def test_get_potentially_not_completed_games_limit_list():
    user_games = UserGameFactory.build_batch(5, total_playtime=120)

    not_completed_games, games_count = get_potentially_not_completed_games(user_games, limit=2)

    assert isinstance(not_completed_games, list)
    assert len(not_completed_games) == 2
    assert games_count == 5
