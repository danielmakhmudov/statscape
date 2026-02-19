import pytest

from core.factories import GenreFactory, ThemeFactory, GameFactory


@pytest.fixture
def genre():
    return GenreFactory()


@pytest.fixture
def theme():
    return ThemeFactory()


@pytest.fixture
def game():
    return GameFactory()
