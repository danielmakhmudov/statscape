from igdb.wrapper import IGDBWrapper
from dotenv import load_dotenv
import os
import json

load_dotenv()

wrapper = IGDBWrapper(os.getenv("IGDB_CLIENT_ID"), os.getenv("IGDB_ACCESS_TOKEN"))


def get_igdb_data(steam_app_ids):
    steam_app_ids = ",".join([f'"{s_id}"' for s_id in steam_app_ids])
    if not steam_app_ids:
        return {}
    byte_igdb_data = wrapper.api_request(
        "external_games",
        f"""fields uid, game.name, game.themes.name, game.themes.id, game.rating, game.cover.url;
         limit 500; where external_game_source = 1 & uid = ({steam_app_ids});""",
    )

    json_igdb_data = json.loads(byte_igdb_data)
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
