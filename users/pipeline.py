from .models import User
from core.services.steam_api_service import SteamAPI
from core.services.user_data_service import update_user_data

steam_api_service = SteamAPI()


def create_steam_user(strategy, details, backend, response=None, user=None, *args, **kwargs):
    if user:
        return {"is_new": False}

    # Получаем Steam ID из response
    identity_url = getattr(response, "identity_url", "")
    steam_id = identity_url.split("/")[-1] if identity_url else None

    if not steam_id:
        return None

    # Получаем дополнительные данные из Steam API
    steam_user_data = steam_api_service.get_user_profile(steam_id)

    # Создаем пользователя с данными из Steam API
    user = User.objects.create_user(
        steam_id=steam_id,
        nickname=steam_user_data.get("personaname", ""),
        avatar_url=steam_user_data.get("avatarfull", ""),
    )

    return {"is_new": True, "user": user}


def update_steam_user_data(strategy, details, backend, user=None, *args, **kwargs):
    if not user or kwargs.get("is_new"):
        return

    update_user_data(user.steam_id)
