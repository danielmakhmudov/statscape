from django.utils import timezone
from core.models import TokenStorage
from dotenv import load_dotenv
import datetime
import os
import logging
import requests

logger = logging.getLogger(__name__)


load_dotenv()


class IGDBClient:
    def get_access_token(self):
        access_token = TokenStorage.objects.filter(service_name="igdb").first()
        current_datetime = timezone.now()
        if access_token and current_datetime < access_token.expires_at:
            return access_token.access_token
        else:
            try:
                url = "https://id.twitch.tv/oauth2/token"
                params = {
                    "client_id": os.getenv("IGDB_CLIENT_ID"),
                    "client_secret": os.getenv("IGDB_CLIENT_SECRET"),
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
