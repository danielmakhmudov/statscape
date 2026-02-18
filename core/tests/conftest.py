import pytest

from core.factories import GenreFactory, ThemeFactory


@pytest.fixture
def genre(db):
    return GenreFactory()


@pytest.fixture
def theme(db):
    return ThemeFactory()
