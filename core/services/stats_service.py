from core.services.user_data_service import get_or_fetch_user_library


def get_account_total_playtime(steam_id):
    games = get_or_fetch_user_library(steam_id=steam_id)
    if not games:
        return 0.0

    account_total_playtime = sum(g.total_playtime for g in games)

    return account_total_playtime
