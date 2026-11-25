import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from users.models import UserRegistrationModel


def is_admin_authenticated(request):
    """Verifies whether the current session has admin privileges."""
    return request.session.get('is_admin', False) is True


def AdminLoginCheck(request):
    """
    Administrator authentication checking environment-configured or secure credentials.
    Sets session on successful login and clears sensitive credentials.
    """
    if request.method == 'POST':
        usrid = request.POST.get('loginid', '').strip()
        pswd = request.POST.get('pswd', '').strip()

        expected_admin_user = os.environ.get('ADMIN_LOGIN_ID', 'admin')
        expected_admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin')

        if usrid == expected_admin_user and pswd == expected_admin_pass:
            request.session['is_admin'] = True
            request.session['admin_user'] = usrid
            return redirect('adminhome')
        else:
            messages.error(request, 'Invalid administrator credentials.')

    return render(request, 'AdminLogin.html', {})


def adminhome(request):
    """Admin dashboard overview."""
    if not is_admin_authenticated(request):
        messages.warning(request, 'Please log in as administrator to access this console.')
        return redirect('AdminLogin')

    total_users = UserRegistrationModel.objects.count()
    activated_users = UserRegistrationModel.objects.filter(status='activated').count()
    pending_users = UserRegistrationModel.objects.filter(status='waiting').count()

    return render(request, 'admins/AdminHome.html', {
        'admin_user': request.session.get('admin_user', 'Admin'),
        'total_users': total_users,
        'activated_users': activated_users,
        'pending_users': pending_users,
    })


def RegisterUsersView(request):
    """Auditing queue for reviewing and approving registered users."""
    if not is_admin_authenticated(request):
        messages.warning(request, 'Please log in as administrator to access user management.')
        return redirect('AdminLogin')

    data = UserRegistrationModel.objects.all().order_by('-id')
    return render(request, 'admins/viewregisterusers.html', context={'data': data})


@require_http_methods(["POST", "GET"])
def ActivaUsers(request):
    """
    Activates a registered user account upon administrative review.
    Accepts POST (preferred) or GET (backward compatibility) with valid admin session.
    """
    if not is_admin_authenticated(request):
        messages.error(request, 'Unauthorized action. Admin session required.')
        return redirect('AdminLogin')

    user_id = request.POST.get('uid') or request.GET.get('uid')
    if user_id:
        try:
            user = get_object_or_404(UserRegistrationModel, id=user_id)
            user.status = 'activated'
            user.save()
            messages.success(request, f"User '{user.loginid}' has been successfully activated.")
        except Exception as e:
            messages.error(request, f"Failed to activate user: {str(e)}")

    return redirect('RegisterUsersView')


@require_http_methods(["POST", "GET"])
def DeleteUsers(request):
    """
    Permanently revokes and deletes a user account.
    Accepts POST (preferred) or GET (backward compatibility) with valid admin session.
    """
    if not is_admin_authenticated(request):
        messages.error(request, 'Unauthorized action. Admin session required.')
        return redirect('AdminLogin')

    user_id = request.POST.get('uid') or request.GET.get('uid')
    if user_id:
        try:
            user = get_object_or_404(UserRegistrationModel, id=user_id)
            loginid = user.loginid
            user.delete()
            messages.success(request, f"User '{loginid}' deleted successfully.")
        except Exception as e:
            messages.error(request, f"Failed to delete user: {str(e)}")

    return redirect('RegisterUsersView')


def AdminLogout(request):
    """Logs out administrator and flushes session data."""
    request.session.flush()
    messages.success(request, 'Logged out from administrator portal successfully.')
    return redirect('AdminLogin')


