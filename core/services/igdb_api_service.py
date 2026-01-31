from igdb.wrapper import IGDBWrapper
from dotenv import load_dotenv
import os
import json

load_dotenv()

wrapper = IGDBWrapper(os.getenv("IGDB_CLIENT_ID"), os.getenv("IGDB_ACCESS_TOKEN"))


def get_igdb_data(steam_app_ids):
    steam_app_ids = ",".join([f'"{s_id}"' for s_id in steam_app_ids])
    byte_igdb_data = wrapper.api_request(
        "external_games",
        f"""fields uid, game.name, game.themes.name, game.rating, game.cover.url;
         limit 500; where external_game_source = 1 & uid = ({steam_app_ids});""",
    )

    json_igdb_data = json.loads(byte_igdb_data)
    # igdb_data_map = {json_igdb_data.get("uid"):json_igdb_data.get("game")}
    igdb_data_map = {}
    for game in json_igdb_data:
        igdb_data_map[game.get("uid")] = game.get("game")

    return igdb_data_map
