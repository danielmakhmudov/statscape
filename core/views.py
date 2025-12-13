from django.views.generic import TemplateView
from core.services.user_data_service import get_or_fetch_user_profile, get_or_fetch_user_library
from core.services.stats_service import enrich_games_with_stats, get_chart_data
from django.contrib.auth.mixins import LoginRequiredMixin


class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    redirect_field_name = "next"
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        social = self.request.user.social_auth.get(provider="steam")
        steam_id = social.uid
        user_profile = get_or_fetch_user_profile(steam_id=steam_id)
        user_library = get_or_fetch_user_library(steam_id=steam_id)

        user_library, total_hours = enrich_games_with_stats(user_library)
        chart_labels, chart_values, chart_hours = get_chart_data(user_library)
        context.update(
            {
                "user_profile": user_profile,
                "user_library": user_library,
                "games_count": len(user_library),
                "total_hours": total_hours,
                "chart_labels": chart_labels,
                "chart_values": chart_values,
                "chart_hours": chart_hours,
            }
        )
        return context
