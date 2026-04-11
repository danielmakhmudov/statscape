from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from core.views import DashboardView, LibraryView, UpdateUserDataView


def test_dashboard_view_redirects_anonymous_user_to_login(rf):
    request = rf.get(reverse("dashboard"))
    request.user = AnonymousUser()

    response = DashboardView.as_view()(request)

    assert response.status_code == 302
    parsed_url = urlparse(response.url)
    assert parsed_url.path == "/login/"
    assert parse_qs(parsed_url.query).get("next") == [reverse("dashboard")]


def test_dashboard_view_builds_context_for_authenticated_user(rf, monkeypatch):
    steam_id = "76561198000000000"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.get(reverse("dashboard"))
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)

    user_profile = {"steamid": steam_id, "personaname": "TestUser"}
    initial_library = [{"game": "A"}, {"game": "B"}]
    enriched_library = [{"game": "A", "playtime_hours": 10.0}, {"game": "B", "playtime_hours": 5.0}]
    total_hours = 15.0
    not_played_games = [{"game": "C"}]
    not_completed_games = [{"game": "D"}]
    chart_labels = ["A", "B"]
    chart_values = [66.67, 33.33]
    chart_hours = [10.0, 5.0]
    favorite_games = [{"game": "A"}]
    recent_games = [{"game": "B"}]

    mock_get_or_fetch_user_profile = MagicMock(return_value=user_profile)
    mock_get_or_fetch_user_library = MagicMock(return_value=initial_library)
    mock_get_not_played_games = MagicMock(return_value=(not_played_games, 1))
    mock_enrich_games_with_stats = MagicMock(return_value=(enriched_library, total_hours))
    mock_get_potentially_not_completed_games = MagicMock(return_value=(not_completed_games, 1))
    mock_get_chart_data = MagicMock(return_value=(chart_labels, chart_values, chart_hours))
    mock_get_favorite_games = MagicMock(return_value=favorite_games)
    mock_get_prepared_recently_played_games = MagicMock(return_value=recent_games)

    monkeypatch.setattr("core.views.get_or_fetch_user_profile", mock_get_or_fetch_user_profile)
    monkeypatch.setattr("core.views.get_or_fetch_user_library", mock_get_or_fetch_user_library)
    monkeypatch.setattr("core.views.get_not_played_games", mock_get_not_played_games)
    monkeypatch.setattr("core.views.enrich_games_with_stats", mock_enrich_games_with_stats)
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games",
        mock_get_potentially_not_completed_games,
    )
    monkeypatch.setattr("core.views.get_chart_data", mock_get_chart_data)
    monkeypatch.setattr("core.views.get_favorite_games", mock_get_favorite_games)
    monkeypatch.setattr(
        "core.views.get_prepared_recently_played_games",
        mock_get_prepared_recently_played_games,
    )

    response = DashboardView.as_view()(request)
    context = response.context_data

    assert response.status_code == 200
    assert context["user_profile"] == user_profile
    assert context["user_library"] == enriched_library
    assert context["games_count"] == 2
    assert context["total_hours"] == total_hours
    assert context["chart_labels"] == chart_labels
    assert context["chart_values"] == chart_values
    assert context["chart_hours"] == chart_hours
    assert context["favorite_games"] == favorite_games
    assert context["recent_games"] == recent_games
    assert context["not_played_games"] == not_played_games
    assert context["not_played_games_count"] == 1
    assert context["not_completed_games"] == not_completed_games
    assert context["not_completed_games_count"] == 1

    social_auth.get.assert_called_once_with(provider="steam")
    mock_get_or_fetch_user_profile.assert_called_once_with(steam_id=steam_id)
    mock_get_or_fetch_user_library.assert_called_once_with(steam_id=steam_id)
    mock_get_not_played_games.assert_called_once_with(initial_library, limit=5)
    mock_enrich_games_with_stats.assert_called_once_with(initial_library)
    mock_get_potentially_not_completed_games.assert_called_once_with(enriched_library, limit=5)
    mock_get_chart_data.assert_called_once_with(enriched_library)
    mock_get_favorite_games.assert_called_once_with(enriched_library)
    mock_get_prepared_recently_played_games.assert_called_once_with(enriched_library)


def test_dashboard_view_handles_empty_library_context(rf, monkeypatch):
    steam_id = "76561198000000001"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.get(reverse("dashboard"))
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)

    monkeypatch.setattr(
        "core.views.get_or_fetch_user_profile", MagicMock(return_value={"steamid": steam_id})
    )
    monkeypatch.setattr("core.views.get_or_fetch_user_library", MagicMock(return_value=[]))
    monkeypatch.setattr("core.views.get_not_played_games", MagicMock(return_value=([], 0)))
    monkeypatch.setattr("core.views.enrich_games_with_stats", MagicMock(return_value=([], 0.0)))
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games", MagicMock(return_value=([], 0))
    )
    monkeypatch.setattr("core.views.get_chart_data", MagicMock(return_value=([], [], [])))
    monkeypatch.setattr("core.views.get_favorite_games", MagicMock(return_value=[]))
    monkeypatch.setattr("core.views.get_prepared_recently_played_games", MagicMock(return_value=[]))

    response = DashboardView.as_view()(request)
    context = response.context_data

    assert response.status_code == 200
    assert context["games_count"] == 0
    assert context["user_library"] == []
    assert context["total_hours"] == 0.0
    assert context["chart_labels"] == []
    assert context["chart_values"] == []
    assert context["chart_hours"] == []
    assert context["favorite_games"] == []
    assert context["recent_games"] == []
    assert context["not_played_games"] == []
    assert context["not_played_games_count"] == 0
    assert context["not_completed_games"] == []
    assert context["not_completed_games_count"] == 0


def test_update_user_data_view_redirects_anonymous_user_to_login(rf):
    request = rf.post(reverse("update_user_data"))
    request.user = AnonymousUser()

    response = UpdateUserDataView.as_view()(request)

    assert response.status_code == 302
    parsed_url = urlparse(response.url)
    assert parsed_url.path == "/login/"
    assert parse_qs(parsed_url.query).get("next") == [reverse("update_user_data")]


def test_update_user_data_view_post_updates_data_and_redirects_to_dashboard(rf, monkeypatch):
    steam_id = "76561198000000010"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.post(reverse("update_user_data"))
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)
    mock_update_user_data = MagicMock()
    monkeypatch.setattr("core.views.update_user_data", mock_update_user_data)

    response = UpdateUserDataView.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    social_auth.get.assert_called_once_with(provider="steam")
    mock_update_user_data.assert_called_once_with(steam_id)


def test_update_user_data_view_get_uses_post_logic_and_redirects_to_dashboard(rf, monkeypatch):
    steam_id = "76561198000000011"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.get(reverse("update_user_data"))
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)
    mock_update_user_data = MagicMock()
    monkeypatch.setattr("core.views.update_user_data", mock_update_user_data)

    response = UpdateUserDataView.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    social_auth.get.assert_called_once_with(provider="steam")
    mock_update_user_data.assert_called_once_with(steam_id)


def test_library_view_redirects_anonymous_user_to_login(rf):
    request = rf.get(reverse("library"))
    request.user = AnonymousUser()

    response = LibraryView.as_view()(request)

    assert response.status_code == 302
    parsed_url = urlparse(response.url)
    assert parsed_url.path == "/login/"
    assert parse_qs(parsed_url.query).get("next") == [reverse("library")]


def test_library_view_builds_context_without_filter(rf, monkeypatch):
    steam_id = "76561198000000100"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.get(reverse("library"))
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)

    raw_library = [{"game": "A"}, {"game": "B"}]
    enriched_library = [{"game": "A", "playtime_hours": 10.0}, {"game": "B", "playtime_hours": 5.0}]
    mock_get_or_fetch_user_library = MagicMock(return_value=raw_library)
    mock_get_not_played_games = MagicMock()
    mock_get_potentially_not_completed_games = MagicMock()
    mock_enrich_games_with_stats = MagicMock(return_value=(enriched_library, 15.0))

    monkeypatch.setattr("core.views.get_or_fetch_user_library", mock_get_or_fetch_user_library)
    monkeypatch.setattr("core.views.get_not_played_games", mock_get_not_played_games)
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games",
        mock_get_potentially_not_completed_games,
    )
    monkeypatch.setattr("core.views.enrich_games_with_stats", mock_enrich_games_with_stats)

    response = LibraryView.as_view()(request)
    context = response.context_data

    assert response.status_code == 200
    assert context["games_count"] == 2
    assert context["current_filter"] is None
    assert list(context["page_obj"].object_list) == enriched_library

    social_auth.get.assert_called_once_with(provider="steam")
    mock_get_or_fetch_user_library.assert_called_once_with(steam_id=steam_id)
    mock_get_not_played_games.assert_not_called()
    mock_get_potentially_not_completed_games.assert_not_called()
    mock_enrich_games_with_stats.assert_called_once_with(raw_library)


def test_library_view_applies_not_played_filter_before_enrichment(rf, monkeypatch):
    steam_id = "76561198000000101"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.get(f"{reverse('library')}?filter=not_played")
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)

    raw_library = [{"game": "A"}, {"game": "B"}, {"game": "C"}]
    filtered_library = [{"game": "C"}]
    enriched_library = [{"game": "C", "playtime_hours": 0.0}]
    mock_get_or_fetch_user_library = MagicMock(return_value=raw_library)
    mock_get_not_played_games = MagicMock(return_value=(filtered_library, 1))
    mock_get_potentially_not_completed_games = MagicMock()
    mock_enrich_games_with_stats = MagicMock(return_value=(enriched_library, 0.0))

    monkeypatch.setattr("core.views.get_or_fetch_user_library", mock_get_or_fetch_user_library)
    monkeypatch.setattr("core.views.get_not_played_games", mock_get_not_played_games)
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games",
        mock_get_potentially_not_completed_games,
    )
    monkeypatch.setattr("core.views.enrich_games_with_stats", mock_enrich_games_with_stats)

    response = LibraryView.as_view()(request)
    context = response.context_data

    assert response.status_code == 200
    assert context["games_count"] == 1
    assert context["current_filter"] == "not_played"
    assert list(context["page_obj"].object_list) == enriched_library

    mock_get_not_played_games.assert_called_once_with(raw_library)
    mock_get_potentially_not_completed_games.assert_not_called()
    mock_enrich_games_with_stats.assert_called_once_with(filtered_library)


def test_library_view_applies_not_completed_filter_before_enrichment(rf, monkeypatch):
    steam_id = "76561198000000102"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.get(f"{reverse('library')}?filter=not_completed")
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)

    raw_library = [{"game": "A"}, {"game": "B"}, {"game": "C"}]
    filtered_library = [{"game": "B"}]
    enriched_library = [{"game": "B", "playtime_hours": 2.0}]
    mock_get_or_fetch_user_library = MagicMock(return_value=raw_library)
    mock_get_not_played_games = MagicMock()
    mock_get_potentially_not_completed_games = MagicMock(return_value=(filtered_library, 1))
    mock_enrich_games_with_stats = MagicMock(return_value=(enriched_library, 2.0))

    monkeypatch.setattr("core.views.get_or_fetch_user_library", mock_get_or_fetch_user_library)
    monkeypatch.setattr("core.views.get_not_played_games", mock_get_not_played_games)
    monkeypatch.setattr(
        "core.views.get_potentially_not_completed_games",
        mock_get_potentially_not_completed_games,
    )
    monkeypatch.setattr("core.views.enrich_games_with_stats", mock_enrich_games_with_stats)

    response = LibraryView.as_view()(request)
    context = response.context_data

    assert response.status_code == 200
    assert context["games_count"] == 1
    assert context["current_filter"] == "not_completed"
    assert list(context["page_obj"].object_list) == enriched_library

    mock_get_not_played_games.assert_not_called()
    mock_get_potentially_not_completed_games.assert_called_once_with(raw_library)
    mock_enrich_games_with_stats.assert_called_once_with(filtered_library)


def test_library_view_paginates_enriched_library(rf, monkeypatch):
    steam_id = "76561198000000103"
    social_auth = SimpleNamespace(get=MagicMock(return_value=SimpleNamespace(uid=steam_id)))
    request = rf.get(f"{reverse('library')}?page=2")
    request.user = SimpleNamespace(is_authenticated=True, social_auth=social_auth)

    raw_library = [{"game": f"G{i}"} for i in range(30)]
    enriched_library = [{"game": f"G{i}", "playtime_hours": float(i)} for i in range(30)]

    monkeypatch.setattr("core.views.get_or_fetch_user_library", MagicMock(return_value=raw_library))
    monkeypatch.setattr("core.views.get_not_played_games", MagicMock())
    monkeypatch.setattr("core.views.get_potentially_not_completed_games", MagicMock())
    monkeypatch.setattr(
        "core.views.enrich_games_with_stats", MagicMock(return_value=(enriched_library, 0.0))
    )

    response = LibraryView.as_view()(request)
    page_obj = response.context_data["page_obj"]

    assert response.status_code == 200
    assert page_obj.number == 2
    assert page_obj.paginator.count == 30
    assert len(page_obj.object_list) == 6
