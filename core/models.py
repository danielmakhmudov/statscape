from django.db import models
from django.conf import settings


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    total_playtime = models.IntegerField(default=0)
    recent_playtime = models.IntegerField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.game}"

    class Meta:
        unique_together = ("user", "game")
        ordering = ["-last_played"]
