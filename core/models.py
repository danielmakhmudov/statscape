from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomUserManager(BaseUserManager):
    def create_user(self, steam_id, nickname=None, avatar_url=None, **extra_fields):
        if not steam_id:
            raise ValueError("User must have a Steam ID!")
        user = self.model(
            steam_id=steam_id, nickname=nickname, avatar_url=avatar_url, **extra_fields
        )

        user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, steam_id, nickname=None, avatar_url=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(steam_id, nickname, avatar_url, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    steam_id = models.CharField(max_length=64, unique=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "steam_id"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.nickname or f"User {self.steam_id}"


class Genre(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Game(models.Model):
    app_id = models.CharField(max_length=65, unique=True)
    name = models.CharField(max_length=64)
    genres = models.ManyToManyField(Genre, related_name="games")
    logo_url = models.URLField(blank=True, null=True)
    rating = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name


class UserGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    total_playtime = models.IntegerField(default=0)
    recent_playtime = models.IntegerField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.game}"

    class Meta:
        unique_together = ("user", "game")
        ordering = ["-last_played"]
