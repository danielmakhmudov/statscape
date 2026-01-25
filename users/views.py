from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.http import require_POST


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "users/login.html")


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out")
    return redirect("login")


@require_POST
def delete_profile_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user = request.user
    logout(request)
    user.delete()
    return redirect("login")
