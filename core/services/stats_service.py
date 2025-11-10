from core.services.user_data_service import get_or_fetch_user_library


def get_account_total_hours(steam_id):
    games = get_or_fetch_user_library(steam_id=steam_id)
    if not games:
        return 0.0

    total_minutes = sum(g.total_playtime for g in games)

    return round(total_minutes / 60, 2)
