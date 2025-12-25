from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from core.services.user_data_service import (
    get_or_fetch_user_profile,
    get_or_fetch_user_library,
    update_user_data,
)
from core.services.stats_service import (
    enrich_games_with_stats,
    get_chart_data,
    get_favorite_games,
    get_prepared_recently_played_games,
)
from django.contrib.auth.mixins import LoginRequiredMixin


class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    redirect_field_name = "next"
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        steam_id = self.request.user.social_auth.get(provider="steam").uid
        user_profile = get_or_fetch_user_profile(steam_id=steam_id)
        user_library = get_or_fetch_user_library(steam_id=steam_id)

        user_library, total_hours = enrich_games_with_stats(user_library)
        chart_labels, chart_values, chart_hours = get_chart_data(user_library)
        favorite_games = get_favorite_games(user_library)
        recent_games = get_prepared_recently_played_games(user_library)
        context.update(
            {
                "user_profile": user_profile,
                "user_library": user_library,
                "games_count": len(user_library),
                "total_hours": total_hours,
                "chart_labels": chart_labels,
                "chart_values": chart_values,
                "chart_hours": chart_hours,
                "favorite_games": favorite_games,
                "recent_games": recent_games,
            }
        )
        return context


class UpdateUserDataView(LoginRequiredMixin, View):
    login_url = "/login/"
    redirect_field_name = "next"

    def post(self, request, *args, **kwargs):
        steam_id = request.user.social_auth.get(provider="steam").uid
        update_user_data(steam_id)
        return redirect("dashboard")

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
