import os
from dotenv import load_dotenv
import requests
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class SteamAPI:
    def __init__(self):
        self.steam_api_key = os.getenv("STEAM_API_KEY")
        self.base_url = "https://api.steampowered.com"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SteamScape/1.0"})

        if not self.steam_api_key:
            logger.error("STEAM_API_KEY not found in .env")

    def get_user_profile(self, steam_id: str) -> dict:
        endpoint = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {"key": self.steam_api_key, "steamids": steam_id, "format": "json"}

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if "response" in data and "players" in data["response"]:
                return data["response"]["players"][0] if data["response"]["players"] else {}
            return {}

        except requests.RequestException as e:
            logger.error(f"Steam API error for user {steam_id}: {e}")
            return {}

    def get_user_library(self, steam_id: str) -> dict:
        endpoint = f"{self.base_url}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "steamid": steam_id,
            "key": self.steam_api_key,
            "include_appinfo": True,
            "include_played_free_games": True,
            "format": "json",
        }

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if "response" in data and "games" in data["response"]:
                return data["response"]
            return {}

        except requests.RequestException as e:
            logger.error(f"Steam API error for user {steam_id}: {e}")
            return {}
