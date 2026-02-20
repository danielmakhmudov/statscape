import pytest
from core.factories import GenreFactory, ThemeFactory, GameFactory, UserGameFactory


@pytest.fixture
def genre():
    return GenreFactory()


@pytest.fixture
def theme():
    return ThemeFactory()


@pytest.fixture
def game():
    return GameFactory()


@pytest.fixture
def user_game():
    return UserGameFactory()
