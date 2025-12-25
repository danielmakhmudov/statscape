import heapq


def enrich_games_with_stats(games):
    if not games:
        return [], 0.0
    total_playtime = sum(g.total_playtime for g in games) if games else 0
    total_hours = round(total_playtime / 60, 1)
    for g in games:
        g.playtime_percentage = (
            round(g.total_playtime / total_playtime * 100, 1) if total_playtime > 0 else 0
        )
        g.playtime_hours = round(g.total_playtime / 60, 1)
        g.recent_playtime_hours = round(g.recent_playtime / 60, 1)
    games = sorted(games, key=lambda x: x.total_playtime, reverse=True)
    return games, total_hours


def get_chart_data(games):
    top_games = games[:10]
    others = games[10:]
    others_playtime_percentage = sum(g.playtime_percentage for g in others)
    chart_labels = [g.game.name for g in top_games]
    chart_values = [g.playtime_percentage for g in top_games]
    chart_hours = [g.playtime_hours for g in top_games]

    if others_playtime_percentage > 0:
        others_hours = sum(g.playtime_hours for g in others)
        chart_labels.append("Others")
        chart_values.append(others_playtime_percentage)
        chart_hours.append(others_hours)

    return chart_labels, chart_values, chart_hours


def get_favorite_games(games):
    if not games:
        return []
    return games[:5]


def get_prepared_recently_played_games(games):
    if not games:
        return []

    games_with_date = (g for g in games if g.last_played is not None)
    return heapq.nlargest(5, games_with_date, key=lambda x: x.last_played)
