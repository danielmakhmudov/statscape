import pytest
from core.models import Genre


@pytest.mark.django_db
def test_genre_instance_creation():
    genre_instance = Genre.objects.create(name="Action")
    assert str(genre_instance) == "Action"
