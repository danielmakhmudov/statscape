from .models import User
from core.services.steam_api_service import SteamAPI

steam_api_service = SteamAPI()


def create_steam_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {"is_new": False}

    # Получаем Steam ID из response
    steam_id = kwargs.get("response", {}).get("identity_url", "").split("/")[-1]

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

    # Получаем свежие данные из Steam API
    steam_user_data = steam_api_service.get_user_profile(steam_id=user.steam_id)

    if steam_user_data:
        # Обновляем данные только если они изменились
        updated = False

        new_nickname = steam_user_data.get("personaname", "")
        if new_nickname and user.nickname != new_nickname:
            user.nickname = new_nickname
            updated = True

        new_avatar = steam_user_data.get("avatarfull", "")
        if new_avatar and user.avatar_url != new_avatar:
            user.avatar_url = new_avatar
            updated = True

        if updated:
            user.save(update_fields=["nickname", "avatar_url"])
