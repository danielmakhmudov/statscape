import pytest

from core.factories import GameFactory, GenreFactory, ThemeFactory


@pytest.mark.django_db
def test_game_factory_sets_extracted_genres():
    genres = GenreFactory.create_batch(2)

    game = GameFactory(genres=genres)

    assert set(game.genres.all()) == set(genres)


@pytest.mark.django_db
def test_game_factory_sets_extracted_themes():
    themes = ThemeFactory.create_batch(2)

    game = GameFactory(themes=themes)

    assert set(game.themes.all()) == set(themes)
