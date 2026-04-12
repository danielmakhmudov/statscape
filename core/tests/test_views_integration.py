from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse


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
