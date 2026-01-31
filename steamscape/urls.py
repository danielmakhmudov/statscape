from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("users.urls")),
    path("auth/", include("social_django.urls", namespace="social")),
]
