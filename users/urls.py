from django.urls import path
from users import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("delete_profile/", views.delete_profile_view, name="delete_profile"),
]
