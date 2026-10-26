from .models import Notification, HostelAnnouncement


def hostel_global_context(request):
    """
    Globally injects unread notifications and latest hostel announcements
    into all rendered templates.
    """
    if not request.user.is_authenticated:
        return {
            'header_notifications': [],
            'unread_notifications_count': 0,
            'header_announcements': [],
        }

    unread_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:8]
    unread_count = request.user.notifications.filter(is_read=False).count()
    header_announcements = HostelAnnouncement.objects.filter(is_active=True).order_by('-created_at')[:5]

    return {
        'header_notifications': unread_notifications,
        'unread_notifications_count': unread_count,
        'header_announcements': header_announcements,
    }
