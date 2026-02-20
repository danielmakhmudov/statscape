import factory
import datetime
from factory.django import DjangoModelFactory
from users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    steam_id = factory.Sequence(lambda n: f"{n}")
    nickname = factory.Sequence(lambda n: f"Name_{n}")
    realname = factory.Sequence(lambda n: f"Name_{n} Surname_{n}")
    avatar_url = factory.Sequence(lambda n: f"https://avatar_url-{n}.com")
    steam_user_since = factory.Faker("date_time_this_decade", tzinfo=datetime.timezone.utc)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.objects.create_user(**kwargs)
