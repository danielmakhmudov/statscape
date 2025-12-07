from core.services.steam_api_service import SteamAPI
from users.models import User
from core.models import UserGame, Game
from django.db import transaction
from datetime import datetime, timezone as dt_timezone
import logging

logger = logging.getLogger(__name__)


def get_or_fetch_user_profile(steam_id):
    try:
        return User.objects.get(steam_id=steam_id)
    except User.DoesNotExist:
        steam_api = SteamAPI()
        user_data = steam_api.get_user_profile(steam_id)
        if not user_data:
            return None

        user_profile = User.objects.create(
            steam_id=user_data.get("steamid"),
            nickname=user_data.get("personaname"),
            realname=user_data.get("realname"),
            avatar_url=user_data.get("avatarfull"),
        )

        return user_profile


def get_or_fetch_user_library(steam_id, force_update=False):
    try:
        user = User.objects.get(steam_id=steam_id)
    except User.DoesNotExist:
        return UserGame.objects.none()

    if not force_update:
        user_games = UserGame.objects.filter(user=user)
        if user_games.exists():
            return user_games

    steam_api = SteamAPI()
    data = steam_api.get_user_library(steam_id=user.steam_id)
    games = data.get("games") if isinstance(data, dict) else None
    if not games:
        return UserGame.objects.none()

    with transaction.atomic():
        for g in games:
            app_id = g.get("appid")
            if not app_id:
                logger.warning(f"Skipped game without appid : {g.get('name', 'Unknown')}")
                continue

            app_id = str(app_id)
            name = g.get("name") or ""
            img_logo = g.get("img_icon_url")
            logo_url = (
                f"https://media.steampowered.com/steamcommunity/public/images/apps/"
                f"{app_id}/{img_logo}.jpg"
                if img_logo
                else None
            )

            total_playtime = g.get("playtime_forever", 0)
            recent_playtime = g.get("playtime_2weeks", 0)

            rtime = g.get("rtime_last_played")
            last_played = datetime.fromtimestamp(int(rtime), tz=dt_timezone.utc) if rtime else None

            game, _ = Game.objects.get_or_create(
                app_id=app_id,
                defaults={
                    "name": name,
                    "logo_url": logo_url,
                },
            )

            UserGame.objects.update_or_create(
                user=user,
                game=game,
                defaults={
                    "total_playtime": total_playtime,
                    "recent_playtime": recent_playtime,
                    "last_played": last_played,
                },
            )
    return UserGame.objects.filter(user=user).select_related("game")
