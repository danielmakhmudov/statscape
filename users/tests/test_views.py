import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_login_view_redirects_authenticated_user_to_dashboard(authenticated_client):
    response = authenticated_client.get(reverse("login"))

    assert response.status_code == 302
    assert response.url == reverse("dashboard")


@pytest.mark.django_db
def test_login_view_renders_login_template_for_anonymous_user(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert "users/login.html" in [template.name for template in response.templates]


@pytest.mark.django_db
def test_login_view_post_anonymous_user_returns_405(client):
    response = client.post(reverse("login"))

    assert response.status_code == 405
