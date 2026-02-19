import pytest

from core.factories import GenreFactory, ThemeFactory, GameFactory


@pytest.fixture
def genre(db):
    return GenreFactory()


@pytest.fixture
def theme(db):
    return ThemeFactory()


@pytest.fixture
def game(db):
    return GameFactory()
