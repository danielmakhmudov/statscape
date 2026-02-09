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


class IGDBClient:
    def __init__(self, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET):
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

    def get_igdb_data(self, steam_app_ids):
        if not steam_app_ids:
            return {}
        ACCESS_TOKEN = self.get_access_token()
        wrapper = IGDBWrapper(self.IGDB_CLIENT_ID, ACCESS_TOKEN)

        json_igdb_data = []
        for chunk in chunk_list(steam_app_ids, 500):
            steam_app_ids_string = ",".join([f'"{s_id}"' for s_id in chunk])
            byte_igdb_data = wrapper.api_request(
                "external_games",
                f"""fields uid, game.name, game.themes.name, game.themes.id, game.rating,
                game.cover.url; limit 500;
                where external_game_source = 1 & uid = ({steam_app_ids_string});""",
            )
            json_igdb_data.extend(json.loads(byte_igdb_data))

        igdb_data_map = {}

        igdb_game_ids = set()

        for g in json_igdb_data:
            if not g.get("game", {}).get("id") or not g.get("uid"):
                continue
            igdb_game_ids.add(g.get("game", {}).get("id"))
        igdb_game_ids_string = ",".join([f"{gid}" for gid in igdb_game_ids])
        if igdb_game_ids_string:
            time_to_beat_data = wrapper.api_request(
                "game_time_to_beats",
                f"fields game_id, normally; limit 500; where game_id = ({igdb_game_ids_string});",
            )
            time_to_beat_data = json.loads(time_to_beat_data)
        else:
            time_to_beat_data = []
        time_to_beat_map = {}
        for game in time_to_beat_data:
            if not game.get("game_id"):
                continue
            time_to_beat_map[str(game.get("game_id"))] = game

        for game in json_igdb_data:
            key = str(game.get("uid"))
            igdb_game = game.get("game", {})
            if not key or not igdb_game:
                continue
            igdb_data_map[key] = igdb_game
            igdb_game_id = str(igdb_game.get("id"))
            time_to_beat_sec = time_to_beat_map.get(igdb_game_id, {}).get("normally", 0)
            time_to_beat_h = round(time_to_beat_sec / 3600, 1)
            igdb_data_map[key]["time_to_beat"] = time_to_beat_h
        return igdb_data_map
