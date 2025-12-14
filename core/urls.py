from django.urls import path
from core import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("update_user_data/", views.UpdateUserDataView.as_view(), name="update_user_data"),
]
