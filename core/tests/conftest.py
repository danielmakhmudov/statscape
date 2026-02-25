import pytest
from core.factories import (
    GenreFactory,
    ThemeFactory,
    GameFactory,
    UserGameFactory,
    TokenStorageFactory,
)


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
def user_game_list():
    return UserGameFactory.build_batch(5)


@pytest.fixture
def user_game():
    return UserGameFactory.build()


@pytest.fixture
def token_storage():
    return TokenStorageFactory()
