import factory
from factory.django import DjangoModelFactory
from core.models import Genre, Theme


class GenreFactory(DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Sequence(lambda n: f"Genre_{n}")


class ThemeFactory(DjangoModelFactory):
    class Meta:
        model = Theme

    igdb_id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Theme_{n}")
