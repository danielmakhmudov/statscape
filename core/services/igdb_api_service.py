from django.utils import timezone
from core.models import TokenStorage
from core.services.utils import chunk_list
from igdb.wrapper import IGDBWrapper
from dotenv import load_dotenv
import datetime
import logging
import requests
import json

logger = logging.getLogger(__name__)


load_dotenv()


class ConfigurationError(Exception):
    pass


class IGDBClient:
    def __init__(self, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET):
        if (
            not IGDB_CLIENT_ID
            or not IGDB_CLIENT_ID.strip()
            or not IGDB_CLIENT_SECRET
            or not IGDB_CLIENT_SECRET.strip()
        ):
            logger.error("IGDB_CLIENT_ID or IGDB_CLIENT_SECRET isn't found")
            raise ConfigurationError("IGDB_CLIENT_ID and IGDB_CLIENT_SECRET are required")

        self.IGDB_CLIENT_ID = IGDB_CLIENT_ID
        self.IGDB_CLIENT_SECRET = IGDB_CLIENT_SECRET

    def get_access_token(self):
        access_token = TokenStorage.objects.filter(service_name="igdb").first()
        current_datetime = timezone.now()
        if access_token and current_datetime < access_token.expires_at:
            return access_token.access_token
        else:
            try:
                url = "https://id.twitch.tv/oauth2/token"
                params = {
                    "client_id": self.IGDB_CLIENT_ID,
                    "client_secret": self.IGDB_CLIENT_SECRET,
                    "grant_type": "client_credentials",
                }
                response = requests.post(url=url, params=params)
                if response.status_code == 200:
                    igdb_access_token_info = response.json()
                    access_token = igdb_access_token_info.get("access_token")
                    expires_in_sec = igdb_access_token_info.get("expires_in")
                    if not isinstance(access_token, str) or not access_token.strip():
                        logger.error("Error: invalid access_token value in IGDB response")
                        raise ValueError("Invalid IGDB token payload: missing access_token")
                    if not isinstance(expires_in_sec, (int, float)):
                        logger.error("Error: invalid expires_in value in IGDB response")
                        raise ValueError("Invalid IGDB token payload: invalid expires_in")
                    expires_at = current_datetime + datetime.timedelta(seconds=expires_in_sec)

                    token_obj, created = TokenStorage.objects.update_or_create(
                        service_name="igdb",
                        defaults={
                            "access_token": access_token,
                            "expires_at": expires_at,
                            "updated_at": current_datetime,
                        },
                    )
                    return token_obj.access_token
                else:
                    logger.error(
                        f"IGDB token request failed with status code: {response.status_code}"
                    )
                    raise Exception(f"Failed to get IGDB token: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error: Failed to get IGDB ACCESS TOKEN: {e}")
                raise

    def _get_igdb_basic_game_data(self, steam_app_ids, wrapper):
        json_igdb_data = []
        for chunk in chunk_list(steam_app_ids, 500):
            steam_app_ids_string = ",".join([f'"{s_id}"' for s_id in chunk])
            if steam_app_ids_string:
                byte_igdb_data = wrapper.api_request(
                    "external_games",
                    f"""fields uid, game.name, game.themes.name, game.themes.id, game.rating,
                        game.cover.url; limit 500;
                        where external_game_source = 1 & uid = ({steam_app_ids_string});""",
                )
                json_igdb_data.extend(json.loads(byte_igdb_data))
            else:
                continue
        return json_igdb_data

    def _get_igdb_time_to_beat_data(self, igdb_game_ids, wrapper):
        time_to_beat_data = []
        for chunk in chunk_list(igdb_game_ids, 500):
            igdb_game_ids_string = ",".join([f"{gid}" for gid in chunk])
            if igdb_game_ids_string:
                byte_time_to_beat_data = wrapper.api_request(
                    "game_time_to_beats",
                    f"""fields game_id, normally; limit 500;
                        where game_id = ({igdb_game_ids_string});""",
                )
                time_to_beat_data.extend(json.loads(byte_time_to_beat_data))
            else:
                continue

        return time_to_beat_data

    def get_igdb_data(self, steam_app_ids):
        if not steam_app_ids:
            return {}
        ACCESS_TOKEN = self.get_access_token()
        wrapper = IGDBWrapper(self.IGDB_CLIENT_ID, ACCESS_TOKEN)
        json_igdb_data = self._get_igdb_basic_game_data(steam_app_ids, wrapper)
        igdb_game_ids = self.get_igdb_game_ids(json_igdb_data)
        time_to_beat_data = self._get_igdb_time_to_beat_data(igdb_game_ids, wrapper)
        time_to_beat_map = self.get_time_to_beat_map(time_to_beat_data)
        igdb_data_map = self.get_merged_igdb_data(json_igdb_data, time_to_beat_map)

        return igdb_data_map

    @staticmethod
    def get_igdb_game_ids(json_igdb_data):
        igdb_game_ids = set()
        for g in json_igdb_data:
            if not g.get("game", {}).get("id") or not g.get("uid"):
                continue
            igdb_game_ids.add(g.get("game", {}).get("id"))
        return igdb_game_ids

    @staticmethod
    def get_time_to_beat_map(time_to_beat_data):
        time_to_beat_map = {}
        for game in time_to_beat_data:
            if not game.get("game_id"):
                continue
            time_to_beat_map[str(game.get("game_id"))] = game
        return time_to_beat_map

    @staticmethod
    def get_merged_igdb_data(json_igdb_data, time_to_beat_map):
        igdb_data_map = {}

        for game in json_igdb_data:
            raw_key = game.get("uid")
            igdb_game = game.get("game", {})
            if not raw_key or not igdb_game:
                continue
            key = str(raw_key)
            igdb_data_map[key] = igdb_game
            igdb_game_id = str(igdb_game.get("id"))
            time_to_beat_sec = time_to_beat_map.get(igdb_game_id, {}).get("normally", 0)
            time_to_beat_h = round(time_to_beat_sec / 3600, 1)
            igdb_data_map[key]["time_to_beat"] = time_to_beat_h
        return igdb_data_map
