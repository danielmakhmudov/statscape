from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "users/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out")
    return redirect("login")
