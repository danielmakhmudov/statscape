from core.services.stats_service import enrich_games_with_stats
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
