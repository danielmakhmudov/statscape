from django.urls import path
from core import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view()),
]
