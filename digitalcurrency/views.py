from django.shortcuts import render


def index(request):
    """Platform landing page."""
    return render(request, 'index.html', {})


def AdminLogin(request):
    """Administrator portal login entrypoint."""
    return render(request, 'AdminLogin.html', {})


def UserLogin(request):
    """User / Analyst authentication portal entrypoint."""
    return render(request, 'UserLogin.html', {})
