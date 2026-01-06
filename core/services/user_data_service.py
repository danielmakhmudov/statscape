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

        timecreated = user_data.get("timecreated")
        steam_user_since = (
            datetime.fromtimestamp(int(timecreated), tz=dt_timezone.utc) if timecreated else None
        )

        user_profile = User.objects.create(
            steam_id=user_data.get("steamid"),
            nickname=user_data.get("personaname"),
            realname=user_data.get("realname"),
            avatar_url=user_data.get("avatarfull"),
            steam_user_since=steam_user_since,
        )

        return user_profile


def update_user_data(steam_id):
    steam_api = SteamAPI()
    user_data = steam_api.get_user_profile(steam_id)
    if user_data:
        try:
            user = User.objects.get(steam_id=steam_id)
            timecreated = user_data.get("timecreated")
            steam_user_since = (
                datetime.fromtimestamp(int(timecreated), tz=dt_timezone.utc)
                if timecreated
                else None
            )

            user.nickname = user_data.get("personaname")
            user.realname = user_data.get("realname")
            user.avatar_url = user_data.get("avatarfull")
            user.steam_user_since = steam_user_since
            user.save()

            get_or_fetch_user_library(steam_id, force_update=True)
            return user

        except User.DoesNotExist:
            logger.warning(f"User with steam_id {steam_id} not found for update")
            return None
    return None


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
    api_games_map = {}
    for g in games:
        app_id = g.get("appid")
        if not app_id:
            logger.warning(f"Skipped game without appid: {g.get('name', 'Unknown')}")
            continue
        api_games_map[str(app_id)] = g

    if not api_games_map:
        return UserGame.objects.none()

    game_instances = []
    for app_id, g in api_games_map.items():
        name = g.get("name") or ""
        img_logo = g.get("img_icon_url")
        logo_url = (
            f"https://media.steampowered.com/steamcommunity/public/images/apps/"
            f"{app_id}/{img_logo}.jpg"
            if img_logo
            else None
        )

        game_instances.append(Game(app_id=app_id, name=name, logo_url=logo_url))
    if not game_instances:
        return UserGame.objects.none()

    with transaction.atomic():
        Game.objects.bulk_create(
            game_instances,
            update_conflicts=True,
            unique_fields=["app_id"],
            update_fields=["name", "logo_url"],
            batch_size=1000,
        )

        games_in_db = Game.objects.filter(app_id__in=api_games_map.keys())
        game_map = {g.app_id: g for g in games_in_db}

        user_game_instances = []

        for app_id, g in api_games_map.items():
            game_obj = game_map.get(app_id)
            if not game_obj:
                continue

            total_playtime = g.get("playtime_forever", 0)
            recent_playtime = g.get("playtime_2weeks", 0)

            rtime = g.get("rtime_last_played")
            last_played = datetime.fromtimestamp(int(rtime), tz=dt_timezone.utc) if rtime else None

            user_game_instances.append(
                UserGame(
                    user=user,
                    game=game_obj,
                    total_playtime=total_playtime,
                    recent_playtime=recent_playtime,
                    last_played=last_played,
                )
            )
        if not user_game_instances:
            return UserGame.objects.none()

        UserGame.objects.bulk_create(
            user_game_instances,
            update_conflicts=True,
            unique_fields=["user", "game"],
            update_fields=["total_playtime", "recent_playtime", "last_played"],
            batch_size=1000,
        )
        return UserGame.objects.filter(user=user).select_related("game")
