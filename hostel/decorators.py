from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles=None):
    """
    Decorator to restrict view access to specific user roles.
    Redirects with a warning message if the user does not have permission.
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(request, "Please log in to access this page.")
                return redirect('login')

            # Superusers always have access
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "You do not have authorization to view that requested page.")
            return redirect('dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Convenience decorator for System Administrator / SuperAdmin only."""
    return role_required(['ADMIN'])(view_func)


def chief_warden_or_admin_required(view_func):
    """Convenience decorator for Chief Warden and System Administrator."""
    return role_required(['ADMIN', 'CHIEF_WARDEN'])(view_func)


def chief_warden_required(view_func):
    """Convenience decorator for Chief Warden only."""
    return role_required(['CHIEF_WARDEN'])(view_func)


def warden_or_admin_required(view_func):
    """Convenience decorator for Staff, Wardens, Chief Wardens, and Admins."""
    return role_required(['ADMIN', 'CHIEF_WARDEN', 'WARDEN'])(view_func)


def warden_required(view_func):
    """Convenience decorator for Wardens only."""
    return role_required(['WARDEN'])(view_func)


def student_required(view_func):
    """Convenience decorator for Students / Residents only."""
    return role_required(['STUDENT'])(view_func)
