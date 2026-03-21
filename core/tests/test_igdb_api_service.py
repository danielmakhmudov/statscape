import pytest
import logging
from core.services.igdb_api_service import ConfigurationError, IGDBClient


def test_init_success():
    igdb_client_instance = IGDBClient(
        IGDB_CLIENT_ID="fake-igdb_client_id", IGDB_CLIENT_SECRET="fake-igdb_client_secret"
    )

    assert igdb_client_instance.IGDB_CLIENT_ID == "fake-igdb_client_id"
    assert igdb_client_instance.IGDB_CLIENT_SECRET == "fake-igdb_client_secret"


@pytest.mark.parametrize(
    "IGDB_CLIENT_ID, IGDB_CLIENT_SECRET",
    [
        (None, "fake-igdb_client_secret"),
        ("fake-igdb_client_id", None),
        (None, None),
        ("", ""),
        (" ", " "),
        (" ", "fake-igdb_client_secret"),
        ("fake-igdb_client_id", " "),
    ],
    ids=[
        "without_client_id",
        "without_client_secret",
        "client_id_and_secret_are_none",
        "client_id_and_secret_are_empty_strings",
        "client_id_and_secret_are_whitespaces",
        "client_id_is_whitespace",
        "client_secret_is_whitespace",
    ],
)
def test_init_configuration_error(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, caplog):
    with caplog.at_level(logging.ERROR):
        with pytest.raises(
            ConfigurationError, match="IGDB_CLIENT_ID and IGDB_CLIENT_SECRET are required"
        ):
            IGDBClient(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)

    assert "IGDB_CLIENT_ID or IGDB_CLIENT_SECRET isn't found" in caplog.text
