import pytest
from unittest.mock import MagicMock
from core.services.user_data_service import get_or_fetch_user_profile
from users.factories import UserFactory


@pytest.mark.django_db
def test_get_or_fetch_user_profile_user_in_db():
    UserFactory.create(steam_id="123")

    user_profile = get_or_fetch_user_profile(steam_id="123")

    assert user_profile.steam_id == "123"


def test_get_or_fetch_user_profile_missing_user_in_db(monkeypatch, steam_api_instance):
    mock_data = {}
    mock_api = MagicMock(return_value=mock_data)
    monkeypatch.setattr("core.services.user_data_service.SteamAPI", MagicMock())
    monkeypatch.setattr(
        "core.services.user_data_service.SteamAPI.get_user_profile",
        MagicMock(return_value=mock_api),
    )
