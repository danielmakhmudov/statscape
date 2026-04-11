import pytest
from django.contrib.messages import get_messages
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


@pytest.mark.django_db
def test_logout_view_post_authenticated_user_redirects_to_login_and_logs_out(authenticated_client):
    response = authenticated_client.post(reverse("logout"))

    assert response.status_code == 302
    assert response.url == reverse("login")
    assert "_auth_user_id" not in authenticated_client.session
    assert [message.message for message in get_messages(response.wsgi_request)] == [
        "Successfully logged out"
    ]


@pytest.mark.django_db
def test_logout_view_post_anonymous_user_redirects_to_login(client):
    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert response.url == reverse("login")
    assert [message.message for message in get_messages(response.wsgi_request)] == []


@pytest.mark.django_db
def test_logout_view_get_returns_405(client):
    response = client.get(reverse("logout"))

    assert response.status_code == 405


@pytest.mark.django_db
def test_delete_profile_view_post_authenticated_user_deletes_user_and_redirects(
    authenticated_client, user
):
    response = authenticated_client.post(reverse("delete_profile"))

    assert response.status_code == 302
    assert response.url == reverse("login")
    assert "_auth_user_id" not in authenticated_client.session
    assert not user.__class__.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_delete_profile_view_post_anonymous_user_redirects_to_login_and_does_not_delete_user(
    client, user
):
    response = client.post(reverse("delete_profile"))

    assert response.status_code == 302
    assert response.url == reverse("login")
    assert user.__class__.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_delete_profile_view_get_returns_405(client):
    response = client.get(reverse("delete_profile"))

    assert response.status_code == 405
