import pytest
from core.services.stats_service import enrich_games_with_stats, get_chart_data
from core.factories import UserGameFactory


def test_enrich_games_with_stats_basic(user_game_list):
    enriched_games, total_hours = enrich_games_with_stats(user_game_list)

    assert total_hours == 5
    assert enriched_games[0].playtime_percentage == 20
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
    user_games = UserGameFactory.build_batch(10)
    enriched_games, _ = enrich_games_with_stats(user_games)

    chart_labels, chart_values, chart_hours = get_chart_data(enriched_games)

    assert len(chart_labels) == len(chart_values) == len(chart_hours) == 10
    assert "Others" not in chart_labels


def test_get_chart_data_more_than_10_but_others_zero_percent():
    user_games = UserGameFactory.build_batch(10) + UserGameFactory.build_batch(
        5, recent_playtime=0, total_playtime=0
    )
    enriched_games, _ = enrich_games_with_stats(user_games)

    chart_labels, chart_values, chart_hours = get_chart_data(enriched_games)

    assert len(chart_labels) == len(chart_values) == len(chart_hours) == 10
    assert "Others" not in chart_labels


def test_get_chart_data_empty_list():
    chart_labels, chart_values, chart_hours = get_chart_data([])

    assert chart_labels == []
    assert chart_values == []
    assert chart_hours == []
