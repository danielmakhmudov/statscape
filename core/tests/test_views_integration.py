from urllib.parse import parse_qs, urlparse
from unittest.mock import MagicMock

import pytest
from django.urls import reverse
from social_django.models import UserSocialAuth

from users.factories import UserFactory


@pytest.mark.django_db
def test_dashboard_redirects_anonymous_user_to_login_with_next(client):
    response = client.get(reverse("dashboard"))

    assert response.status_code == 302
    parsed_url = urlparse(response.url)
    assert parsed_url.path == "/login/"
    assert parse_qs(parsed_url.query).get("next") == [reverse("dashboard")]


@pytest.mark.django_db
def test_library_redirects_anonymous_user_to_login_with_next(client):
    response = client.get(reverse("library"))

    assert response.status_code == 302
    parsed_url = urlparse(response.url)
    assert parsed_url.path == "/login/"
    assert parse_qs(parsed_url.query).get("next") == [reverse("library")]


@pytest.mark.django_db
def test_update_user_data_post_redirects_anonymous_user_to_login_with_next(client):
    response = client.post(reverse("update_user_data"))

    assert response.status_code == 302
    parsed_url = urlparse(response.url)
    assert parsed_url.path == "/login/"
    assert parse_qs(parsed_url.query).get("next") == [reverse("update_user_data")]


@pytest.mark.django_db
def test_update_user_data_get_redirects_anonymous_user_to_login_with_next(client):
    response = client.get(reverse("update_user_data"))

    assert response.status_code == 302
    parsed_url = urlparse(response.url)
    assert parsed_url.path == "/login/"
    assert parse_qs(parsed_url.query).get("next") == [reverse("update_user_data")]


@pytest.mark.django_db
def test_dashboard_renders_for_authenticated_user_with_social_auth(client, monkeypatch):
    user = UserFactory()
    steam_id = "76561198001234567"
    UserSocialAuth.objects.create(user=user, provider="steam", uid=steam_id)
    client.force_login(user)

    monkeypatch.setattr(
        "core.views.get_or_fetch_user_profile",
        lambda steam_id: {"steamid": steam_id, "personaname": "TestUser"},
    )
    monkeypatch.setattr("core.views.get_or_fetch_user_library", lambda steam_id: [])
    monkeypatch.setattr("core.views.get_not_played_games", lambda user_library, limit=5: ([], 0))
    monkeypatch.setattr("core.views.enrich_games_with_stats", lambda user_library: ([], 0.0))
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games",
        lambda user_library, limit=5: ([], 0),
    )
    monkeypatch.setattr("core.views.get_chart_data", lambda user_library: ([], [], []))
    monkeypatch.setattr("core.views.get_favorite_games", lambda user_library: [])
    monkeypatch.setattr("core.views.get_prepared_recently_played_games", lambda user_library: [])

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert "core/dashboard.html" in [template.name for template in response.templates]
    assert response.context["user_profile"]["steamid"] == steam_id
    assert response.context["games_count"] == 0


@pytest.mark.django_db
def test_library_renders_for_authenticated_user_with_social_auth(client, monkeypatch):
    user = UserFactory()
    steam_id = "76561198001234568"
    UserSocialAuth.objects.create(user=user, provider="steam", uid=steam_id)
    client.force_login(user)

    library = [{"name": "Game A"}, {"name": "Game B"}]
    monkeypatch.setattr("core.views.get_or_fetch_user_library", lambda steam_id: library)
    monkeypatch.setattr("core.views.enrich_games_with_stats", lambda user_library: (library, 10.0))
    monkeypatch.setattr("core.views.get_not_played_games", lambda user_library: ([], 0))
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games",
        lambda user_library: ([], 0),
    )

    response = client.get(reverse("library"))

    assert response.status_code == 200
    assert "core/library.html" in [template.name for template in response.templates]
    assert response.context["games_count"] == 2
    assert response.context["current_filter"] is None
    assert response.context["page_obj"] is not None


@pytest.mark.django_db
def test_library_filter_not_played_sets_current_filter_for_authenticated_user(client, monkeypatch):
    user = UserFactory()
    steam_id = "76561198001234569"
    UserSocialAuth.objects.create(user=user, provider="steam", uid=steam_id)
    client.force_login(user)

    library = [{"name": "Game A"}, {"name": "Game B"}]
    filtered_library = [{"name": "Game B"}]
    mock_get_not_played_games = MagicMock(return_value=(filtered_library, 1))

    monkeypatch.setattr("core.views.get_or_fetch_user_library", lambda steam_id: library)
    monkeypatch.setattr("core.views.get_not_played_games", mock_get_not_played_games)
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games",
        lambda user_library: ([], 0),
    )
    monkeypatch.setattr(
        "core.views.enrich_games_with_stats",
        lambda user_library: (filtered_library, 5.0),
    )

    response = client.get(f"{reverse('library')}?filter=not_played")

    assert response.status_code == 200
    assert response.context["current_filter"] == "not_played"
    assert response.context["games_count"] == 1
    mock_get_not_played_games.assert_called_once_with(library)


@pytest.mark.django_db
def test_update_user_data_post_redirects_authenticated_user_to_dashboard(client, monkeypatch):
    user = UserFactory()
    steam_id = "76561198001234570"
    UserSocialAuth.objects.create(user=user, provider="steam", uid=steam_id)
    client.force_login(user)
    mock_update_user_data = MagicMock()
    monkeypatch.setattr("core.views.update_user_data", mock_update_user_data)

    response = client.post(reverse("update_user_data"))

    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    mock_update_user_data.assert_called_once_with(steam_id)
