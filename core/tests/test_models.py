import pytest
from core.models import Genre, Theme


@pytest.mark.django_db
def test_genre_model():
    genre_instance = Genre.objects.create(name="Action")
    assert str(genre_instance) == "Action"


@pytest.mark.django_db
def test_theme_model():
    theme_instance = Theme.objects.create(igdb_id=100, name="Action")
    assert str(theme_instance) == "Action"
    assert theme_instance.igdb_id == 100
