import pytest


@pytest.mark.django_db
def test_genre_model(genre):
    assert str(genre) == genre.name


@pytest.mark.django_db
def test_theme_model(theme):
    assert str(theme) == theme.name
    assert isinstance(theme.igdb_id, int)


# @pytest.mark.django_db
# def test_game_model():
