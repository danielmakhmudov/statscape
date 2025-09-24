from core.services.steam_api_service import SteamAPI
from users.models import User


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
            avatar_url=user_data.get("avatarfull"),
        )

        return user_profile
