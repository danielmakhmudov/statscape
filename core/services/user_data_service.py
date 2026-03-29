from core.services.steam_api_service import SteamAPI
from users.models import User
from core.models import UserGame, Game, Theme
from django.db import transaction
from datetime import datetime, timezone as dt_timezone
from core.services.igdb_api_service import IGDBClient
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


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
    igdb_client = IGDBClient(
        IGDB_CLIENT_ID=os.getenv("IGDB_CLIENT_ID"),
        IGDB_CLIENT_SECRET=os.getenv("IGDB_CLIENT_SECRET"),
    )
    data = steam_api.get_user_library(steam_id=user.steam_id)
    games = data.get("games") if isinstance(data, dict) else None
    if not games:
        return UserGame.objects.none()
    api_games_map = {}
    steam_app_ids = []
    for g in games:
        app_id = g.get("appid")
        if not app_id:
            logger.warning(f"Skipped game without appid: {g.get('name', 'Unknown')}")
            continue
        steam_app_ids.append(str(app_id))
        api_games_map[str(app_id)] = g

    if not api_games_map:
        return UserGame.objects.none()

    igdb_data_map = igdb_client.get_igdb_data(steam_app_ids)
    themes_list = []
    for t in igdb_data_map.values():
        themes_list.extend(t.get("themes", []))
    unique_themes = {}
    for t in themes_list:
        name = t.get("name", None)
        igdb_id = t.get("id", None)
        if name and igdb_id:
            unique_themes[igdb_id] = t
    themes_objects = [
        Theme(igdb_id=t.get("id"), name=t.get("name")) for t in unique_themes.values()
    ]

    game_instances = []
    for app_id, g in api_games_map.items():
        name = g.get("name") or ""

        rating = igdb_data_map.get(app_id, {}).get("rating", 0.0)
        time_to_beat = igdb_data_map.get(app_id, {}).get("time_to_beat", 0.0)
        img_logo = g.get("img_icon_url")
        logo_url = (
            f"https://media.steampowered.com/steamcommunity/public/images/apps/"
            f"{app_id}/{img_logo}.jpg"
            if img_logo
            else None
        )
        header_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg"

        game_instances.append(
            Game(
                app_id=app_id,
                name=name,
                logo_url=logo_url,
                header_url=header_url,
                rating=rating,
                time_to_beat=time_to_beat,
            )
        )
    if not game_instances:
        return UserGame.objects.none()

    with transaction.atomic():
        Theme.objects.bulk_create(
            themes_objects,
            update_conflicts=True,
            unique_fields=["igdb_id"],
            update_fields=["name"],
            batch_size=1000,
        )
        themes_in_db = Theme.objects.filter(igdb_id__in=unique_themes.keys())
        themes_map = {t.igdb_id: t for t in themes_in_db}

        Game.objects.bulk_create(
            game_instances,
            update_conflicts=True,
            unique_fields=["app_id"],
            update_fields=["name", "logo_url", "header_url", "rating", "time_to_beat"],
            batch_size=1000,
        )

        games_in_db = Game.objects.filter(app_id__in=api_games_map.keys())
        game_map = {g.app_id: g for g in games_in_db}
        game_theme_relations = []
        for uid, game in igdb_data_map.items():
            game_obj = game_map.get(uid)
            if not game_obj:
                continue
            for t in game.get("themes", []):
                theme_obj = themes_map.get(t.get("id"))
                if theme_obj:
                    game_theme_relations.append(
                        Game.themes.through(game_id=game_obj.id, theme_id=theme_obj.id)
                    )
        if game_theme_relations:
            Game.themes.through.objects.bulk_create(
                game_theme_relations,
                ignore_conflicts=True,
                batch_size=1000,
            )

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
        return (
            UserGame.objects.filter(user=user)
            .select_related("game")
            .prefetch_related("game__themes")
        )
