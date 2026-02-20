import pytest


@pytest.mark.django_db
def test_genre_model(genre):
    assert str(genre) == genre.name


@pytest.mark.django_db
def test_theme_model(theme):
    assert str(theme) == theme.name


@pytest.mark.django_db
def test_game_model(game):
    assert str(game) == game.name


@pytest.mark.django_db
def test_user_game_model(user_game):
    assert str(user_game) == f"{user_game.user} - {user_game.game}"
