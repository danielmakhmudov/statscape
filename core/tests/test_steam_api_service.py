import logging
import pytest
from core.services.steam_api_service import SteamAPI, ConfigurationError


def test_steam_api_init_with_api_key(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "fake-key")
    steam_api_instance = SteamAPI()

    assert steam_api_instance.base_url == "https://api.steampowered.com"
    assert steam_api_instance.steam_api_key == "fake-key"
    assert steam_api_instance.session.headers["User-Agent"] == "Statscape/1.0"


def test_steam_api_init_without_api_key(monkeypatch, caplog):
    monkeypatch.delenv("STEAM_API_KEY", raising=False)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ConfigurationError, match="STEAM_API_KEY is required"):
            SteamAPI()

    assert "STEAM_API_KEY not found in .env" in caplog.text
