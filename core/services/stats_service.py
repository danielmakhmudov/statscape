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

    return games, total_hours
