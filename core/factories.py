import factory
from factory.django import DjangoModelFactory
from core.models import Genre, Theme, Game


class GenreFactory(DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Sequence(lambda n: f"Genre_{n}")


class ThemeFactory(DjangoModelFactory):
    class Meta:
        model = Theme

    igdb_id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Theme_{n}")


class GameFactory(DjangoModelFactory):
    class Meta:
        model = Game

    app_id = factory.Sequence(lambda n: f"{n}")
    name = factory.Sequence(lambda n: f"Game_{n}")
    logo_url = factory.Sequence(lambda n: f"https://logo-{n}.com")
    header_url = factory.Sequence(lambda n: f"https://header-{n}.com")
    rating = 100
    time_to_beat = 100

    @factory.post_generation
    def genres(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.genres.set(extracted)
        else:
            self.genres.set(GenreFactory.create_batch(3))

    @factory.post_generation
    def themes(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.themes.set(extracted)
        else:
            self.themes.set(ThemeFactory.create_batch(3))
