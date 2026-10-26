import csv
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Count, Q, IntegerField
from django.db.models.functions import Cast
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from .models import (
    User, Hostel, Block, Room, Bed, Allotment,
    FeeVoucher, Complaint, GatePass, MessSchedule,
    RoomChangeRequest, Notification, HostelAnnouncement
)
from .forms import (
    LoginForm, StudentRegistrationForm, StudentProfileUpdateForm,
    StudentApplicationReviewForm, StaffUserForm, AllotmentForm,
    VacateForm, FeeVoucherCreateForm, BulkFeeGenerateForm,
    FeePaymentProofForm, FeeVerificationForm, ComplaintForm,
    ComplaintUpdateForm, RoomChangeRequestForm, RoomChangeWardenReviewForm,
    RoomChangeAdminProcessForm, HostelAnnouncementForm, RoomMaintenanceForm,
    GatePassRequestForm, GatePassReviewForm, MessScheduleForm,
    HostelForm, RoomForm, StudentFeeVoucherUploadForm, StudentCNICSearchForm
)
from .decorators import (
    role_required, admin_required, chief_warden_or_admin_required,
    chief_warden_required, warden_or_admin_required, warden_required, student_required
)


# ==========================================
# AUTHENTICATION & PROFILE
# ==========================================

def get_user_portal_url(user):
    """Returns the dedicated portal view name based on user's authorized role."""
    if user.is_admin_user:
        return 'admin_portal'
    elif user.is_chief_warden_user:
        return 'chief_warden_portal'
    elif user.is_warden_user:
        return 'warden_portal'
    else:
        return 'student_portal'


def user_login(request):
    """
    One common login page for all users (Students, Wardens, Chief Wardens, Administrators).
    Automatically routes each user to their authorized portal after successful authentication.
    """
    if request.user.is_authenticated:
        return redirect(get_user_portal_url(request.user))

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='hostel.backends.RollNumberOrUsernameBackend')
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            
            # Security-checked next parameter
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and next_url not in ['/', '/dashboard/', reverse('dashboard')]:
                # Ensure students cannot jump into administrative portals via ?next=
                restricted_for_student = ['/portal/admin/', '/portal/chief-warden/', '/portal/warden/', '/admin/', '/wardens/', '/allocations/new/']
                if user.is_student_user and any(r in next_url for r in restricted_for_student):
                    return redirect('student_portal')
                if user.is_warden_user and '/portal/chief-warden/' in next_url:
                    return redirect('warden_portal')
                return redirect(next_url)
            
            return redirect(get_user_portal_url(user))
        else:
            messages.error(request, "Invalid Roll Number or User ID / password. Please verify your credentials and try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def user_register(request):
    """Resident / Student Self-Registration View."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Send welcome notification
            Notification.send(
                recipient=user,
                title="Welcome to Ali Hall Hostel Portal",
                message="Your hostel admission application has been registered. You can track your admission status here.",
                notification_type=Notification.Type.APPLICATION,
                link_url='/profile/'
            )
            login(request, user, backend='hostel.backends.RollNumberOrUsernameBackend')
            messages.success(request, "Registration successful! Your hostel application is now under review.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def user_logout(request):
    """User Logout View."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def profile_view(request):
    """Student Profile View and Document Upload."""
    user = request.user
    active_allotment = user.active_allotment if user.is_student_user else None

    if request.method == 'POST':
        form = StudentProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your personal information and documents have been updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please fix the errors in your profile form.")
    else:
        form = StudentProfileUpdateForm(instance=user)

    context = {
        'user': user,
        'active_allotment': active_allotment,
        'form': form,
    }
    return render(request, 'accounts/profile.html', context)


# ==========================================
# NOTIFICATIONS SYSTEM
# ==========================================

@login_required
def notifications_list(request):
    """View all system notifications for current user."""
    notifications = request.user.notifications.all().order_by('-created_at')
    # Mark visible notifications as read on visit
    request.user.notifications.filter(is_read=False).update(is_read=True)

    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications/notification_list.html', {'page_obj': page_obj})


@login_required
def notification_mark_read(request, pk):
    """Mark single notification as read."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect('notifications_list')


@login_required
def notification_mark_all_read(request):
    """Mark all unread notifications as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ==========================================
# ==========================================
# SMART DASHBOARDS ROUTER & SEPARATE PORTALS
# ==========================================

@login_required
def dashboard_router(request):
    """
    Automatic Role-Based Portal Redirection:
    - Students -> Student Portal (/portal/student/)
    - Wardens -> Warden Portal (/portal/warden/)
    - Chief Wardens -> Chief Warden Portal (/portal/chief-warden/)
    - Administrators -> Admin Portal (/portal/admin/)
    """
    return redirect(get_user_portal_url(request.user))


@login_required
@admin_required
def admin_portal_view(request):
    """
    Dedicated Admin Portal:
    Access all system modules, manage student records, search students by CNIC,
    view fee vouchers & verifications, manage 300 rooms & allocations, and admin functions.
    """
    # High-level statistics
    total_rooms = Room.objects.count()
    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.filter(status=Bed.Status.OCCUPIED).count()
    available_beds = Bed.objects.filter(status=Bed.Status.AVAILABLE).count()
    maintenance_beds = Bed.objects.filter(status=Bed.Status.MAINTENANCE).count()
    occupancy_pct = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0

    total_students = User.objects.filter(role=User.Role.STUDENT).count()
    pending_applications_count = User.objects.filter(role=User.Role.STUDENT, application_status=User.ApplicationStatus.PENDING).count()
    pending_complaints_count = Complaint.objects.filter(status__in=[Complaint.Status.SUBMITTED, Complaint.Status.UNDER_REVIEW, Complaint.Status.IN_PROGRESS]).count()
    pending_room_changes_count = RoomChangeRequest.objects.filter(status__in=[RoomChangeRequest.Status.SUBMITTED, RoomChangeRequest.Status.UNDER_REVIEW, RoomChangeRequest.Status.WARDEN_RECOMMENDED]).count()
    pending_gate_passes_count = GatePass.objects.filter(status=GatePass.Status.PENDING).count()

    # Fee Vouchers Telemetry
    all_vouchers = FeeVoucher.objects.all()
    total_vouchers_count = all_vouchers.count()
    pending_fee_verifications = all_vouchers.filter(status=FeeVoucher.Status.PENDING_VERIFICATION).select_related('student')
    pending_fee_count = pending_fee_verifications.count()
    paid_vouchers_count = all_vouchers.filter(status=FeeVoucher.Status.PAID).count()
    rejected_vouchers_count = all_vouchers.filter(status=FeeVoucher.Status.REJECTED).count()
    unpaid_vouchers_count = all_vouchers.filter(status__in=[FeeVoucher.Status.UNPAID, FeeVoucher.Status.OVERDUE]).count()
    total_collected_amount = all_vouchers.filter(status=FeeVoucher.Status.PAID).aggregate(total=Sum('amount'))['total'] or 0

    # Recent items
    recent_applications = User.objects.filter(role=User.Role.STUDENT).order_by('-application_date')[:5]
    recent_complaints = Complaint.objects.select_related('student', 'assigned_to').order_by('-created_at')[:5]
    recent_room_changes = RoomChangeRequest.objects.select_related('student', 'current_room', 'current_bed').order_by('-created_at')[:5]
    recent_allotments = Allotment.objects.filter(is_active=True).select_related('student', 'room', 'bed').order_by('-created_at')[:5]
    recent_announcements = HostelAnnouncement.objects.filter(is_active=True).order_by('-created_at')[:4]
    cnic_form = StudentCNICSearchForm()

    context = {
        'total_rooms': total_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'maintenance_beds': maintenance_beds,
        'occupancy_pct': occupancy_pct,
        'total_students': total_students,
        'pending_applications_count': pending_applications_count,
        'pending_complaints_count': pending_complaints_count,
        'pending_room_changes_count': pending_room_changes_count,
        'pending_gate_passes_count': pending_gate_passes_count,
        'total_vouchers_count': total_vouchers_count,
        'pending_fee_count': pending_fee_count,
        'paid_vouchers_count': paid_vouchers_count,
        'rejected_vouchers_count': rejected_vouchers_count,
        'unpaid_vouchers_count': unpaid_vouchers_count,
        'total_collected_amount': total_collected_amount,
        'pending_fee_verifications': pending_fee_verifications[:6],
        'recent_applications': recent_applications,
        'recent_complaints': recent_complaints,
        'recent_room_changes': recent_room_changes,
        'recent_allotments': recent_allotments,
        'recent_announcements': recent_announcements,
        'cnic_form': cnic_form,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


# Preserved alias for backwards compatibility
admin_dashboard_view = admin_portal_view


@login_required
@chief_warden_or_admin_required
def chief_warden_portal_view(request):
    """
    Dedicated Chief Warden Portal:
    Oversee hostel operations across all wings/blocks, monitor wardens and staff roster,
    access authorized student and hostel records, view fee collection summaries.
    """
    ali_hall = Hostel.objects.first()
    blocks = Block.objects.filter(hostel=ali_hall).prefetch_related('rooms__beds') if ali_hall else Block.objects.all()

    # Blocks statistics breakdown
    blocks_data = []
    for b in blocks:
        total_b_rooms = b.rooms.count()
        total_b_beds = Bed.objects.filter(room__block=b).count()
        occ_b_beds = Bed.objects.filter(room__block=b, status=Bed.Status.OCCUPIED).count()
        avail_b_beds = Bed.objects.filter(room__block=b, status=Bed.Status.AVAILABLE).count()
        occ_rate = round((occ_b_beds / total_b_beds * 100), 1) if total_b_beds > 0 else 0
        blocks_data.append({
            'block': b,
            'total_rooms': total_b_rooms,
            'total_beds': total_b_beds,
            'occupied_beds': occ_b_beds,
            'available_beds': avail_b_beds,
            'occupancy_rate': occ_rate,
        })

    # High-level metrics
    total_rooms = Room.objects.count()
    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.filter(status=Bed.Status.OCCUPIED).count()
    available_beds = Bed.objects.filter(status=Bed.Status.AVAILABLE).count()
    occupancy_pct = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0
    total_students = User.objects.filter(role=User.Role.STUDENT).count()

    # Wardens monitoring roster
    wardens = User.objects.filter(role__in=[User.Role.WARDEN, User.Role.CHIEF_WARDEN]).select_related(
        'assigned_hostel', 'assigned_block'
    ).annotate(
        assigned_complaints_count=Count('assigned_complaints', filter=Q(assigned_complaints__status__in=[Complaint.Status.SUBMITTED, Complaint.Status.UNDER_REVIEW, Complaint.Status.IN_PROGRESS]))
    ).order_by('role', 'username')

    # Escalated room change requests
    escalated_transfers = RoomChangeRequest.objects.filter(
        status__in=[RoomChangeRequest.Status.SUBMITTED, RoomChangeRequest.Status.UNDER_REVIEW, RoomChangeRequest.Status.WARDEN_RECOMMENDED]
    ).select_related('student', 'current_room', 'current_bed', 'reviewed_by_warden').order_by('-created_at')[:6]

    # Urgent complaints across all blocks
    urgent_complaints = Complaint.objects.filter(
        priority__in=[Complaint.Priority.URGENT, Complaint.Priority.HIGH],
        status__in=[Complaint.Status.SUBMITTED, Complaint.Status.UNDER_REVIEW, Complaint.Status.IN_PROGRESS]
    ).select_related('student', 'assigned_to').order_by('-priority', '-created_at')[:6]

    # Fee summary
    all_vouchers = FeeVoucher.objects.all()
    total_billed = all_vouchers.aggregate(total=Sum('amount'))['total'] or 0
    total_collected = all_vouchers.filter(status=FeeVoucher.Status.PAID).aggregate(total=Sum('amount'))['total'] or 0
    pending_vouchers_count = all_vouchers.filter(status=FeeVoucher.Status.PENDING_VERIFICATION).count()
    unpaid_vouchers_count = all_vouchers.filter(status__in=[FeeVoucher.Status.UNPAID, FeeVoucher.Status.OVERDUE]).count()

    cnic_form = StudentCNICSearchForm()

    context = {
        'total_rooms': total_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'occupancy_pct': occupancy_pct,
        'total_students': total_students,
        'blocks_data': blocks_data,
        'wardens': wardens,
        'escalated_transfers': escalated_transfers,
        'urgent_complaints': urgent_complaints,
        'total_billed': total_billed,
        'total_collected': total_collected,
        'pending_vouchers_count': pending_vouchers_count,
        'unpaid_vouchers_count': unpaid_vouchers_count,
        'cnic_form': cnic_form,
    }
    return render(request, 'dashboard/chief_warden_dashboard.html', context)


@login_required
@warden_or_admin_required
def warden_portal_view(request):
    """
    Dedicated Warden Portal:
    Wardens manage their assigned hostel operations and access student information
    they are authorized to view within their assigned block/wing.
    """
    warden = request.user
    assigned_block = warden.assigned_block

    # Scope rooms and beds to warden's block if assigned, or all Ali Hall
    rooms_qs = Room.objects.filter(block=assigned_block) if assigned_block else Room.objects.all()
    beds_qs = Bed.objects.filter(room__in=rooms_qs)

    total_rooms = rooms_qs.count()
    occupied_beds = beds_qs.filter(status=Bed.Status.OCCUPIED).count()
    available_beds = beds_qs.filter(status=Bed.Status.AVAILABLE).count()

    # Complaints assigned to this warden or in their block
    complaints_qs = Complaint.objects.select_related('student', 'assigned_to')
    if assigned_block:
        complaints_qs = complaints_qs.filter(Q(assigned_to=warden) | Q(student__allotments__room__block=assigned_block)).distinct()
    pending_complaints = complaints_qs.filter(status__in=[Complaint.Status.SUBMITTED, Complaint.Status.UNDER_REVIEW, Complaint.Status.IN_PROGRESS])

    # Room-change requests pending warden recommendation
    room_changes_qs = RoomChangeRequest.objects.select_related('student', 'current_room', 'current_bed')
    if assigned_block:
        room_changes_qs = room_changes_qs.filter(current_room__block=assigned_block)
    pending_room_changes = room_changes_qs.filter(status__in=[RoomChangeRequest.Status.SUBMITTED, RoomChangeRequest.Status.UNDER_REVIEW])

    # Gate passes pending approval
    gate_passes_qs = GatePass.objects.filter(status=GatePass.Status.PENDING).select_related('student')
    if assigned_block:
        gate_passes_qs = gate_passes_qs.filter(student__allotments__room__block=assigned_block, student__allotments__is_active=True).distinct()

    # Recent active students in block
    active_residents = Allotment.objects.filter(is_active=True)
    if assigned_block:
        active_residents = active_residents.filter(room__block=assigned_block)
    active_residents = active_residents.select_related('student', 'room', 'bed').order_by('-allotment_date')[:8]

    # Fee vouchers for residents in this block requiring verification
    block_vouchers = FeeVoucher.objects.select_related('student')
    if assigned_block:
        block_vouchers = block_vouchers.filter(student__allotments__room__block=assigned_block, student__allotments__is_active=True).distinct()
    pending_fee_proofs = block_vouchers.filter(status=FeeVoucher.Status.PENDING_VERIFICATION)[:5]

    announcements = HostelAnnouncement.objects.filter(is_active=True).order_by('-created_at')[:4]

    context = {
        'warden': warden,
        'assigned_block': assigned_block,
        'total_rooms': total_rooms,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'pending_complaints_count': pending_complaints.count(),
        'pending_room_changes_count': pending_room_changes.count(),
        'pending_gate_passes_count': gate_passes_qs.count(),
        'recent_complaints': pending_complaints[:5],
        'recent_room_changes': pending_room_changes[:5],
        'pending_gate_passes': gate_passes_qs[:5],
        'pending_fee_proofs': pending_fee_proofs,
        'active_residents': active_residents,
        'announcements': announcements,
    }
    return render(request, 'dashboard/warden_dashboard.html', context)


# Preserved alias for backwards compatibility
warden_dashboard_view = warden_portal_view


@login_required
@student_required
def student_portal_view(request):
    """
    Dedicated Student Portal:
    Students view their own profile, semester information, room assignments,
    fee details, and uploaded fee vouchers with upload capability.
    """
    student = request.user
    active_allotment = student.active_allotment

    # Roommates in the same room (only Name, Department, Bed - no sensitive personal info)
    roommates = []
    if active_allotment:
        roommates = Allotment.objects.filter(
            room=active_allotment.room,
            is_active=True
        ).exclude(student=student).select_related('student', 'bed')

    # Fee Vouchers & Payment Records
    all_student_vouchers = student.fee_vouchers.all().order_by('-due_date')
    pending_vouchers = all_student_vouchers.filter(
        status__in=[FeeVoucher.Status.UNPAID, FeeVoucher.Status.OVERDUE, FeeVoucher.Status.PENDING_VERIFICATION]
    )
    unpaid_total = all_student_vouchers.filter(
        status__in=[FeeVoucher.Status.UNPAID, FeeVoucher.Status.OVERDUE]
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Voucher upload form
    voucher_upload_form = StudentFeeVoucherUploadForm()

    # Complaints statistics
    complaints = student.complaints.all().order_by('-created_at')
    total_complaints = complaints.count()
    pending_complaints = complaints.filter(status__in=[Complaint.Status.SUBMITTED, Complaint.Status.UNDER_REVIEW, Complaint.Status.IN_PROGRESS]).count()
    resolved_complaints = complaints.filter(status=Complaint.Status.RESOLVED).count()

    # Active room change request if any
    active_room_change = student.room_change_requests.order_by('-created_at').first()

    # Gate passes
    student_gate_passes = student.gate_passes.all().order_by('-created_at')[:4]

    # Recent notifications & announcements
    recent_notifications = student.notifications.all().order_by('-created_at')[:5]
    announcements = HostelAnnouncement.objects.filter(is_active=True).order_by('-created_at')[:4]

    # Today's mess schedule
    current_day = timezone.now().strftime('%A').upper()
    todays_menu = MessSchedule.objects.filter(day_of_week=current_day).order_by('meal_type')

    context = {
        'student': student,
        'active_allotment': active_allotment,
        'roommates': roommates,
        'all_student_vouchers': all_student_vouchers,
        'pending_vouchers': pending_vouchers,
        'unpaid_total': unpaid_total,
        'voucher_upload_form': voucher_upload_form,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'resolved_complaints': resolved_complaints,
        'recent_complaints': complaints[:4],
        'active_room_change': active_room_change,
        'student_gate_passes': student_gate_passes,
        'recent_notifications': recent_notifications,
        'announcements': announcements,
        'todays_menu': todays_menu,
        'current_day': current_day,
    }
    return render(request, 'dashboard/student_dashboard.html', context)


# Preserved alias for backwards compatibility
student_dashboard_view = student_portal_view


# ==========================================
# STUDENT APPLICATIONS MANAGEMENT
# ==========================================

@login_required
@warden_or_admin_required
def application_list(request):
    """Review student hostel admission applications."""
    status_filter = request.GET.get('status', 'PENDING')
    search_query = request.GET.get('q', '').strip()

    students = User.objects.filter(role=User.Role.STUDENT).select_related('reviewed_by')

    if status_filter:
        students = students.filter(application_status=status_filter)

    if search_query:
        students = students.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(registration_no__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(cnic_or_id__icontains=search_query)
        )

    students = students.order_by('-application_date')

    paginator = Paginator(students, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    counts = {
        'pending': User.objects.filter(role=User.Role.STUDENT, application_status=User.ApplicationStatus.PENDING).count(),
        'approved': User.objects.filter(role=User.Role.STUDENT, application_status=User.ApplicationStatus.APPROVED).count(),
        'rejected': User.objects.filter(role=User.Role.STUDENT, application_status=User.ApplicationStatus.REJECTED).count(),
        'allocated': User.objects.filter(role=User.Role.STUDENT, application_status=User.ApplicationStatus.ALLOCATED).count(),
    }

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'counts': counts,
    }
    return render(request, 'applications/application_list.html', context)


@login_required
@warden_or_admin_required
def application_detail(request, pk):
    """Application detail view with document preview and approve/reject actions."""
    student = get_object_or_404(User, pk=pk, role=User.Role.STUDENT)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('application_notes', '').strip()

        if action in ['APPROVE', 'REJECT']:
            with transaction.atomic():
                new_status = User.ApplicationStatus.APPROVED if action == 'APPROVE' else User.ApplicationStatus.REJECTED
                student.application_status = new_status
                student.application_notes = notes
                student.reviewed_by = request.user
                student.reviewed_at = timezone.now()
                student.save()

                # Dispatch notification to student
                Notification.send(
                    recipient=student,
                    title=f"Hostel Application {student.get_application_status_display()}",
                    message=f"Your hostel admission application has been {student.get_application_status_display().lower()} by {request.user.get_full_name() or request.user.username}. {notes}",
                    notification_type=Notification.Type.APPLICATION,
                    link_url='/profile/'
                )

            messages.success(request, f"Application for {student.get_full_name() or student.username} marked as {student.get_application_status_display()}.")
            return redirect('application_list')

    return render(request, 'applications/application_detail.html', {'student': student})


# ==========================================
# STUDENT DIRECTORY
# ==========================================

@login_required
@warden_or_admin_required
def student_directory(request):
    """Complete searchable Student Directory with profile photos and academic details."""
    search_query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()

    students = User.objects.filter(role=User.Role.STUDENT).prefetch_related('allotments__room', 'allotments__bed')

    if search_query:
        students = students.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(registration_no__icontains=search_query) |
            Q(cnic__icontains=search_query) |
            Q(cnic_or_id__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    if dept_filter:
        students = students.filter(department__icontains=dept_filter)

    if status_filter:
        students = students.filter(application_status=status_filter)

    students = students.order_by('username')
    departments = User.objects.filter(role=User.Role.STUDENT).exclude(department='').values_list('department', flat=True).distinct().order_by('department')

    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'dept_filter': dept_filter,
        'status_filter': status_filter,
        'departments': departments,
        'total_students_count': students.count(),
    }
    return render(request, 'students/student_directory.html', context)


@login_required
@warden_or_admin_required
def student_detail_view(request, pk):
    """Full student dossier for administrators and wardens."""
    student = get_object_or_404(User, pk=pk, role=User.Role.STUDENT)
    allotments = student.allotments.select_related('room', 'bed', 'room__block').order_by('-allotment_date')
    complaints = student.complaints.order_by('-created_at')
    room_changes = student.room_change_requests.order_by('-created_at')
    fee_vouchers = student.fee_vouchers.order_by('-due_date')

    context = {
        'student': student,
        'allotments': allotments,
        'complaints': complaints,
        'room_changes': room_changes,
        'fee_vouchers': fee_vouchers,
    }
    return render(request, 'students/student_detail.html', context)


# ==========================================
# STUDENT CNIC SEARCH SYSTEM (ADMIN & CHIEF WARDEN)
# ==========================================

@login_required
@warden_or_admin_required
def student_cnic_search(request):
    """
    Search student by CNIC Number (e.g. 5440166878999 or 54401-6687899-9).
    When the admin searches for a CNIC number, displays all records associated with that student:
    - Student's full name and roll number.
    - CNIC number.
    - Semester details and department.
    - Hostel room number, bed, block, and roommates.
    - Fee vouchers and payment records.
    - Other relevant student information (emergency contact, phone, address, complaints, gate passes).
    """
    cnic_query = (request.GET.get('cnic') or request.POST.get('cnic') or request.GET.get('q', '')).strip()
    student = None
    all_matches = []
    error_message = None

    # If direct student ID provided (from search match selection)
    student_pk = request.GET.get('id')
    if student_pk:
        student = get_object_or_404(User, pk=student_pk, role=User.Role.STUDENT)
        cnic_query = student.cnic or student.cnic_or_id

    elif cnic_query:
        # Normalize: extract pure digits
        clean_digits = ''.join(ch for ch in cnic_query if ch.isdigit())

        # Construct query: exact cnic, clean digits, or cnic_or_id
        q_filter = Q(cnic=cnic_query) | Q(cnic_or_id=cnic_query)
        if clean_digits:
            q_filter |= Q(cnic=clean_digits)
            q_filter |= Q(cnic_or_id__icontains=clean_digits)
        # Fallback to roll number or username
        q_filter |= Q(registration_no__iexact=cnic_query) | Q(username__iexact=cnic_query)

        matched_students = User.objects.filter(role=User.Role.STUDENT).filter(q_filter).distinct()
        match_count = matched_students.count()

        if match_count == 1:
            student = matched_students.first()
        elif match_count > 1:
            all_matches = matched_students
        else:
            error_message = f"No student record found for CNIC / identifier '{cnic_query}'. Please check the CNIC number and try again."

    # If student is identified, fetch complete dossier
    active_allotment = None
    roommates = []
    past_allotments = []
    fee_vouchers = []
    fee_totals = {'billed': 0, 'paid': 0, 'pending': 0, 'rejected': 0, 'unpaid': 0}
    complaints = []
    room_changes = []
    gate_passes = []

    if student:
        active_allotment = student.active_allotment
        if active_allotment:
            roommates = Allotment.objects.filter(
                room=active_allotment.room,
                is_active=True
            ).exclude(student=student).select_related('student', 'bed')

        past_allotments = student.allotments.select_related('room', 'bed', 'room__block').order_by('-created_at')
        fee_vouchers = student.fee_vouchers.select_related('verified_by').order_by('-due_date')

        for v in fee_vouchers:
            fee_totals['billed'] += v.amount
            if v.status == FeeVoucher.Status.PAID:
                fee_totals['paid'] += v.amount
            elif v.status == FeeVoucher.Status.PENDING_VERIFICATION:
                fee_totals['pending'] += v.amount
            elif v.status == FeeVoucher.Status.REJECTED:
                fee_totals['rejected'] += v.amount
            else:
                fee_totals['unpaid'] += v.amount

        fee_totals['balance'] = max(Decimal('0.00'), fee_totals['billed'] - fee_totals['paid'])

        complaints = student.complaints.select_related('assigned_to').order_by('-created_at')
        room_changes = student.room_change_requests.select_related('current_room', 'current_bed', 'preferred_room').order_by('-created_at')
        gate_passes = student.gate_passes.select_related('approved_by').order_by('-created_at')

    context = {
        'cnic_query': cnic_query,
        'student': student,
        'all_matches': all_matches,
        'error_message': error_message,
        'active_allotment': active_allotment,
        'roommates': roommates,
        'past_allotments': past_allotments,
        'fee_vouchers': fee_vouchers,
        'fee_totals': fee_totals,
        'complaints': complaints,
        'room_changes': room_changes,
        'gate_passes': gate_passes,
    }
    return render(request, 'students/cnic_search.html', context)


# ==========================================
# HOSTEL ROOM MANAGEMENT (300 Rooms, 600 Beds)
# ==========================================

@login_required
@warden_or_admin_required
def room_inventory(request):
    """
    Hostel Room Management view supporting 300 rooms with visual grid or table toggle,
    status filtering, quota category (Special Students Rooms 1-100 vs Regular Rooms 101-300),
    bed chips, and complete student details (Name, Mobile, CNIC, Address).
    """
    view_mode = request.GET.get('view', 'grid')  # 'grid' or 'table'
    block_filter = request.GET.get('block', '')
    floor_filter = request.GET.get('floor', '')
    status_filter = request.GET.get('status', '')
    quota_filter = request.GET.get('quota', '')
    search_query = request.GET.get('q', '').strip()
    per_page_param = request.GET.get('per_page', '30')

    rooms = Room.objects.select_related('block', 'block__hostel').prefetch_related(
        'beds', 'allotments__student'
    )

    if block_filter:
        rooms = rooms.filter(block__block_name__icontains=block_filter)

    if floor_filter:
        rooms = rooms.filter(floor=floor_filter)

    if quota_filter == 'SPECIAL':
        rooms = rooms.filter(is_special_quota=True)
    elif quota_filter == 'REGULAR':
        rooms = rooms.filter(is_special_quota=False)

    if search_query:
        rooms = rooms.filter(
            Q(room_number__icontains=search_query) |
            Q(block__block_name__icontains=search_query) |
            Q(allotments__student__first_name__icontains=search_query) |
            Q(allotments__student__last_name__icontains=search_query) |
            Q(allotments__student__phone_number__icontains=search_query) |
            Q(allotments__student__cnic_or_id__icontains=search_query) |
            Q(allotments__student__registration_no__icontains=search_query) |
            Q(allotments__student__address__icontains=search_query)
        ).distinct()

    # Natural integer sorting for room numbers: 1, 2, ..., 99, 100, 101, ... 300
    rooms = rooms.annotate(
        r_num_int=Cast('room_number', output_field=IntegerField())
    ).order_by('floor', 'r_num_int')

    # Filter by occupancy status in Python if needed or keep queryset
    if status_filter == 'AVAILABLE':
        rooms = [r for r in rooms if r.occupancy_status == 'AVAILABLE']
    elif status_filter == 'PARTIAL':
        rooms = [r for r in rooms if r.occupancy_status == 'PARTIALLY_OCCUPIED']
    elif status_filter == 'FULL':
        rooms = [r for r in rooms if r.occupancy_status == 'FULLY_OCCUPIED']
    elif status_filter == 'MAINTENANCE':
        rooms = [r for r in rooms if r.occupancy_status == 'MAINTENANCE']

    total_filtered = len(rooms) if isinstance(rooms, list) else rooms.count()

    # Per page selector
    if per_page_param == 'all':
        per_page = 300
    else:
        try:
            per_page = int(per_page_param)
        except ValueError:
            per_page = 30

    paginator = Paginator(rooms, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    blocks = Block.objects.filter(hostel__name__icontains='Ali Hall').order_by('block_name')

    # Global summary statistics
    all_rooms_list = list(Room.objects.all().prefetch_related('beds'))
    all_beds_list = list(Bed.objects.all())

    stats = {
        'total': len(all_rooms_list),
        'special_rooms': sum(1 for r in all_rooms_list if r.is_special_quota),
        'regular_rooms': sum(1 for r in all_rooms_list if not r.is_special_quota),
        'total_beds': len(all_beds_list),
        'occupied_beds': sum(1 for b in all_beds_list if b.status == Bed.Status.OCCUPIED),
        'vacant_beds': sum(1 for b in all_beds_list if b.status == Bed.Status.AVAILABLE),
        'special_occupied_beds': sum(1 for b in all_beds_list if b.room.is_special_quota and b.status == Bed.Status.OCCUPIED),
        'special_vacant_beds': sum(1 for b in all_beds_list if b.room.is_special_quota and b.status == Bed.Status.AVAILABLE),
        'regular_occupied_beds': sum(1 for b in all_beds_list if not b.room.is_special_quota and b.status == Bed.Status.OCCUPIED),
        'regular_vacant_beds': sum(1 for b in all_beds_list if not b.room.is_special_quota and b.status == Bed.Status.AVAILABLE),
        'available': sum(1 for r in all_rooms_list if r.occupancy_status == 'AVAILABLE'),
        'partial': sum(1 for r in all_rooms_list if r.occupancy_status == 'PARTIALLY_OCCUPIED'),
        'full': sum(1 for r in all_rooms_list if r.occupancy_status == 'FULLY_OCCUPIED'),
        'maintenance': sum(1 for r in all_rooms_list if r.occupancy_status == 'MAINTENANCE'),
    }

    context = {
        'page_obj': page_obj,
        'view_mode': view_mode,
        'block_filter': block_filter,
        'floor_filter': floor_filter,
        'status_filter': status_filter,
        'quota_filter': quota_filter,
        'per_page': per_page_param,
        'search_query': search_query,
        'blocks': blocks,
        'stats': stats,
        'total_filtered': total_filtered,
    }
    return render(request, 'allocations/room_inventory.html', context)


@login_required
@warden_or_admin_required
def room_maintenance_toggle(request, pk):
    """Toggle maintenance status on a room."""
    room = get_object_or_404(Room, pk=pk)
    if room.maintenance_status == Room.MaintenanceStatus.OPERATIONAL:
        room.maintenance_status = Room.MaintenanceStatus.MAINTENANCE
        room.beds.filter(status=Bed.Status.AVAILABLE).update(status=Bed.Status.MAINTENANCE)
        messages.warning(request, f"Room {room.room_number} is now marked as Under Maintenance.")
    else:
        room.maintenance_status = Room.MaintenanceStatus.OPERATIONAL
        room.beds.filter(status=Bed.Status.MAINTENANCE).update(status=Bed.Status.AVAILABLE)
        messages.success(request, f"Room {room.room_number} is now Operational.")
    room.save()
    return redirect(request.META.get('HTTP_REFERER', 'room_inventory'))


@login_required
def get_available_beds_api(request):
    """AJAX endpoint: Returns available beds for a selected room."""
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'beds': []})

    beds = Bed.objects.filter(room_id=room_id, status=Bed.Status.AVAILABLE).values('id', 'bed_code')
    return JsonResponse({'beds': list(beds)})


# ==========================================
# ROOM ALLOCATION (Zero Double-Booking)
# ==========================================

@login_required
@warden_or_admin_required
def allocation_list(request):
    """View active and past bed allocations with filtering."""
    status_filter = request.GET.get('status', 'active')
    search_query = request.GET.get('q', '').strip()
    block_filter = request.GET.get('block', '')

    allotments = Allotment.objects.select_related(
        'student', 'room', 'bed', 'room__block', 'room__block__hostel'
    )

    if status_filter == 'active':
        allotments = allotments.filter(is_active=True)
    elif status_filter == 'vacated':
        allotments = allotments.filter(is_active=False)

    if block_filter:
        allotments = allotments.filter(room__block__block_name__icontains=block_filter)

    if search_query:
        allotments = allotments.filter(
            Q(student__username__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__registration_no__icontains=search_query) |
            Q(student__cnic_or_id__icontains=search_query) |
            Q(room__room_number__icontains=search_query) |
            Q(bed__bed_code__icontains=search_query)
        )

    allotments = allotments.order_by('-allotment_date')

    paginator = Paginator(allotments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    blocks = Block.objects.all()

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'block_filter': block_filter,
        'blocks': blocks,
    }
    return render(request, 'allocations/allocation_list.html', context)


@login_required
@warden_or_admin_required
def allocation_create(request):
    """
    Allocate Bed to a student with Zero Double-Booking validation and atomic updates.
    """
    student_id = request.GET.get('student') or request.GET.get('student_id')
    room_id = request.GET.get('room') or request.GET.get('room_id')
    bed_id = request.GET.get('bed') or request.GET.get('bed_id')
    initial_data = {}
    if student_id:
        initial_data['student'] = student_id
    if room_id:
        initial_data['room'] = room_id
    if bed_id:
        initial_data['bed'] = bed_id

    if request.method == 'POST':
        form = AllotmentForm(request.POST)
        if form.is_valid():
            try:
                allotment = form.save()
                # Notify student
                Notification.send(
                    recipient=allotment.student,
                    title="Hostel Room Allocated",
                    message=f"You have been allocated Room {allotment.room.room_number} ({allotment.bed.bed_code}) in {allotment.room.block.block_name}. Please report to the warden office.",
                    notification_type=Notification.Type.ALLOCATION,
                    link_url='/profile/'
                )
                messages.success(
                    request,
                    f"Successfully allotted Room {allotment.room.room_number} ({allotment.bed.bed_code}) to {allotment.student.get_full_name() or allotment.student.username}."
                )
                return redirect('allocation_list')
            except Exception as e:
                messages.error(request, f"Error saving allotment: {str(e)}")
        else:
            messages.error(request, "Please fix the validation errors below.")
    else:
        form = AllotmentForm(initial=initial_data)

    return render(request, 'allocations/allocation_form.html', {'form': form})


@login_required
@warden_or_admin_required
def allocation_vacate(request, pk):
    """Process bed checkout / vacation atomically."""
    allotment = get_object_or_404(Allotment, pk=pk)

    if not allotment.is_active:
        messages.warning(request, "This allotment record is already vacated.")
        return redirect('allocation_list')

    if request.method == 'POST':
        form = VacateForm(request.POST)
        if form.is_valid():
            vacate_date = form.cleaned_data['vacate_date']
            remarks = form.cleaned_data['remarks']
            allotment.vacate_date = vacate_date
            allotment.vacate(remarks=remarks)
            # Notify student
            Notification.send(
                recipient=allotment.student,
                title="Hostel Room Vacated",
                message=f"Your allotment for Room {allotment.room.room_number} has been officially vacated and closed.",
                notification_type=Notification.Type.ALLOCATION,
                link_url='/profile/'
            )
            messages.success(
                request,
                f"Bed {allotment.bed.bed_code} has been successfully vacated and released back to available status."
            )
            return redirect('allocation_list')
    else:
        form = VacateForm()

    return render(request, 'allocations/allocation_vacate.html', {
        'allotment': allotment,
        'form': form
    })


# ==========================================
# STUDENT ROOM-CHANGE REQUEST WORKFLOW
# ==========================================

@login_required
@student_required
def room_change_request_create(request):
    """Student submits a room-change request."""
    user = request.user
    active_allotment = user.active_allotment

    if not active_allotment:
        messages.error(request, "You do not currently have an active room allocation to request a change.")
        return redirect('dashboard')

    # Prevent multiple pending requests
    existing_pending = user.room_change_requests.filter(
        status__in=[
            RoomChangeRequest.Status.SUBMITTED,
            RoomChangeRequest.Status.UNDER_REVIEW,
            RoomChangeRequest.Status.WARDEN_RECOMMENDED,
            RoomChangeRequest.Status.APPROVED
        ]
    ).exists()

    if existing_pending:
        messages.warning(request, "You already have a pending room-change request under review.")
        return redirect('room_change_list')

    if request.method == 'POST':
        form = RoomChangeRequestForm(request.POST, request.FILES, student_user=user)
        if form.is_valid():
            req = form.save(commit=False)
            req.student = user
            req.current_allotment = active_allotment
            req.current_room = active_allotment.room
            req.current_bed = active_allotment.bed
            req.save()

            # Notify student
            Notification.send(
                recipient=user,
                title="Room Change Request Submitted",
                message=f"Your room change request #{req.request_code} has been submitted and forwarded to the hostel warden for review.",
                notification_type=Notification.Type.ROOM_CHANGE,
                link_url='/room-changes/'
            )
            messages.success(request, f"Room change request #{req.request_code} submitted successfully!")
            return redirect('room_change_list')
    else:
        form = RoomChangeRequestForm(student_user=user)

    context = {
        'form': form,
        'active_allotment': active_allotment,
    }
    return render(request, 'allocations/room_change_form.html', context)


@login_required
def room_change_list(request):
    """List room-change requests (Students see own; Admin/Warden see all)."""
    user = request.user
    status_filter = request.GET.get('status', '')

    if user.is_student_user:
        requests_qs = user.room_change_requests.all()
    elif user.is_warden_user:
        if user.assigned_block:
            requests_qs = RoomChangeRequest.objects.filter(current_room__block=user.assigned_block)
        else:
            requests_qs = RoomChangeRequest.objects.all()
    else:
        requests_qs = RoomChangeRequest.objects.all()

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    requests_qs = requests_qs.select_related('student', 'current_room', 'current_bed', 'preferred_room', 'new_room', 'new_bed').order_by('-created_at')

    paginator = Paginator(requests_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': RoomChangeRequest.Status.choices,
    }
    return render(request, 'allocations/room_change_list.html', context)


@login_required
@warden_or_admin_required
def room_change_detail(request, pk):
    """
    Review Room-Change Request:
    - Warden can add recommendation and remarks.
    - Admin can approve/reject and execute atomic bed transfer.
    """
    req_obj = get_object_or_404(
        RoomChangeRequest.objects.select_related(
            'student', 'current_allotment', 'current_room', 'current_bed',
            'preferred_room', 'new_room', 'new_bed', 'reviewed_by_warden', 'reviewed_by_admin'
        ),
        pk=pk
    )

    warden_form = None
    admin_form = None

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # 1. Warden Recommendation action
        if action_type == 'WARDEN_RECOMMEND' and (request.user.is_warden_user or request.user.is_admin_user):
            warden_form = RoomChangeWardenReviewForm(request.POST, instance=req_obj)
            if warden_form.is_valid():
                obj = warden_form.save(commit=False)
                obj.reviewed_by_warden = request.user
                if obj.warden_recommendation == RoomChangeRequest.WardenRecommendation.RECOMMENDED:
                    obj.status = RoomChangeRequest.Status.WARDEN_RECOMMENDED
                else:
                    obj.status = RoomChangeRequest.Status.WARDEN_NOT_RECOMMENDED
                obj.save()

                Notification.send(
                    recipient=obj.student,
                    title="Room Change Request Reviewed by Warden",
                    message=f"Warden {request.user.get_full_name() or request.user.username} has assessed your request #{obj.request_code} and forwarded findings to the Chief Warden.",
                    notification_type=Notification.Type.ROOM_CHANGE,
                    link_url='/room-changes/'
                )
                messages.success(request, "Warden assessment and recommendation recorded successfully.")
                return redirect('room_change_detail', pk=req_obj.pk)

        # 2. Admin Final Approval & Execution
        elif action_type == 'ADMIN_EXECUTE' and request.user.is_admin_user:
            admin_decision = request.POST.get('status')
            admin_remarks = request.POST.get('admin_remarks', '').strip()
            new_room_id = request.POST.get('new_room')
            new_bed_id = request.POST.get('new_bed')

            if admin_decision == RoomChangeRequest.Status.REJECTED:
                req_obj.status = RoomChangeRequest.Status.REJECTED
                req_obj.admin_remarks = admin_remarks
                req_obj.reviewed_by_admin = request.user
                req_obj.completed_at = timezone.now()
                req_obj.save()

                Notification.send(
                    recipient=req_obj.student,
                    title="Room Change Request Rejected",
                    message=f"Your room change request #{req_obj.request_code} was not approved: {admin_remarks}",
                    notification_type=Notification.Type.ROOM_CHANGE,
                    link_url='/room-changes/'
                )
                messages.warning(request, f"Request #{req_obj.request_code} has been rejected.")
                return redirect('room_change_detail', pk=req_obj.pk)

            elif admin_decision == RoomChangeRequest.Status.APPROVED:
                if not new_room_id or not new_bed_id:
                    messages.error(request, "Please choose an available target Room and Bed to complete the transfer.")
                    return redirect('room_change_detail', pk=req_obj.pk)

                new_room = get_object_or_404(Room, pk=new_room_id)
                new_bed = get_object_or_404(Bed, pk=new_bed_id)

                if new_bed.status != Bed.Status.AVAILABLE:
                    messages.error(request, f"Selected Bed {new_bed.bed_code} is not available.")
                    return redirect('room_change_detail', pk=req_obj.pk)

                # ATOMIC TRANSFER
                with transaction.atomic():
                    # Release old bed
                    old_bed = req_obj.current_bed
                    old_bed.status = Bed.Status.AVAILABLE
                    old_bed.save()

                    # Occupy new bed
                    new_bed.status = Bed.Status.OCCUPIED
                    new_bed.save()

                    # Update student active allotment
                    allotment = req_obj.current_allotment
                    allotment.room = new_room
                    allotment.bed = new_bed
                    allotment.remarks = f"{allotment.remarks}\n[Transferred via #{req_obj.request_code} on {timezone.now().date()}]".strip()
                    allotment.save()

                    # Update request status to COMPLETED
                    req_obj.status = RoomChangeRequest.Status.COMPLETED
                    req_obj.admin_remarks = admin_remarks
                    req_obj.reviewed_by_admin = request.user
                    req_obj.new_room = new_room
                    req_obj.new_bed = new_bed
                    req_obj.completed_at = timezone.now()
                    req_obj.save()

                    # Notify student
                    Notification.send(
                        recipient=req_obj.student,
                        title="Room Transfer Completed",
                        message=f"Congratulations! Your room change has been approved. You are transferred to Room {new_room.room_number} ({new_bed.bed_code}).",
                        notification_type=Notification.Type.ROOM_CHANGE,
                        link_url='/profile/'
                    )

                messages.success(request, f"Transfer completed! {req_obj.student.username} moved to Room {new_room.room_number} ({new_bed.bed_code}).")
                return redirect('room_change_detail', pk=req_obj.pk)

    if not warden_form:
        warden_form = RoomChangeWardenReviewForm(instance=req_obj)
    if not admin_form:
        admin_form = RoomChangeAdminProcessForm(instance=req_obj)

    available_rooms = Room.objects.filter(maintenance_status=Room.MaintenanceStatus.OPERATIONAL).select_related('block')

    context = {
        'req_obj': req_obj,
        'warden_form': warden_form,
        'admin_form': admin_form,
        'available_rooms': available_rooms,
    }
    return render(request, 'allocations/room_change_detail.html', context)


# ==========================================
# STUDENT COMPLAINT SYSTEM (11 Categories)
# ==========================================

@login_required
def complaint_list(request):
    """View complaints list with search and 11-category filtering."""
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('q', '').strip()

    if request.user.is_student_user:
        complaints = request.user.complaints.all()
    elif request.user.is_warden_user and request.user.assigned_block:
        complaints = Complaint.objects.filter(
            Q(assigned_to=request.user) |
            Q(student__allotments__room__block=request.user.assigned_block)
        ).distinct()
    else:
        complaints = Complaint.objects.all()

    complaints = complaints.select_related('student', 'assigned_to', 'resolved_by')

    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if category_filter:
        complaints = complaints.filter(category=category_filter)
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter)
    if search_query:
        complaints = complaints.filter(
            Q(title__icontains=search_query) |
            Q(complaint_ref__icontains=search_query) |
            Q(room_number__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(student__username__icontains=search_query)
        )

    complaints = complaints.order_by('-created_at')

    paginator = Paginator(complaints, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'status_choices': Complaint.Status.choices,
        'category_choices': Complaint.Category.choices,
        'priority_choices': Complaint.Priority.choices,
    }
    return render(request, 'complaints/complaint_list.html', context)


@login_required
@student_required
def complaint_create(request):
    """Student logs a new maintenance ticket."""
    user = request.user
    initial_data = {}
    if user.active_allotment:
        initial_data['room_number'] = user.active_allotment.room.room_number

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = user
            complaint.save()

            # Notify student
            Notification.send(
                recipient=user,
                title="Complaint Ticket Submitted",
                message=f"Complaint #{complaint.complaint_ref} ({complaint.title}) logged. Our maintenance team will attend to it shortly.",
                notification_type=Notification.Type.COMPLAINT,
                link_url=f"/complaints/{complaint.pk}/"
            )

            # Notify warden of block if known
            if user.active_allotment and user.active_allotment.room.block.assigned_wardens.exists():
                warden = user.active_allotment.room.block.assigned_wardens.first()
                Notification.send(
                    recipient=warden,
                    title="New Maintenance Ticket Logged",
                    message=f"New ticket #{complaint.complaint_ref} ({complaint.get_category_display()}) logged for Room {complaint.room_number}.",
                    notification_type=Notification.Type.COMPLAINT,
                    link_url=f"/complaints/{complaint.pk}/"
                )

            messages.success(request, f"Complaint ticket #{complaint.complaint_ref} submitted successfully!")
            return redirect('complaint_list')
    else:
        form = ComplaintForm(initial=initial_data)

    return render(request, 'complaints/complaint_form.html', {'form': form})


@login_required
def complaint_detail(request, pk):
    """Complaint details, assignment, and resolution history."""
    complaint = get_object_or_404(
        Complaint.objects.select_related('student', 'assigned_to', 'resolved_by'),
        pk=pk
    )

    if request.user.is_student_user and complaint.student != request.user:
        messages.error(request, "Unauthorized access.")
        return redirect('complaint_list')

    # If staff/admin/warden, allow assignment and status updates
    if not request.user.is_student_user and request.method == 'POST':
        form = ComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.status == Complaint.Status.RESOLVED:
                updated.resolved_by = request.user
                updated.resolved_at = timezone.now()
            updated.save()

            # Notify student on status change
            Notification.send(
                recipient=complaint.student,
                title=f"Complaint #{complaint.complaint_ref} {updated.get_status_display()}",
                message=f"Your complaint ticket #{complaint.complaint_ref} status was updated to: {updated.get_status_display()}. Remarks: {updated.warden_remarks}",
                notification_type=Notification.Type.COMPLAINT,
                link_url=f"/complaints/{complaint.pk}/"
            )

            messages.success(request, f"Complaint #{complaint.complaint_ref} updated to {updated.get_status_display()}.")
            return redirect('complaint_detail', pk=complaint.pk)
    else:
        form = ComplaintUpdateForm(instance=complaint)

    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint,
        'form': form
    })


# ==========================================
# WARDEN MANAGEMENT (Admin Only)
# ==========================================

@login_required
@admin_required
def warden_list(request):
    """Admin view to manage hostel wardens and permissions."""
    wardens = User.objects.filter(role=User.Role.WARDEN).select_related('assigned_block', 'assigned_hostel').order_by('username')
    return render(request, 'wardens/warden_list.html', {'wardens': wardens})


@login_required
@admin_required
def warden_create(request):
    """Admin view to create a new warden account."""
    if request.method == 'POST':
        form = StaffUserForm(request.POST, request.FILES)
        if form.is_valid():
            warden = form.save()
            messages.success(request, f"Warden account for {warden.get_full_name() or warden.username} created successfully.")
            return redirect('warden_list')
    else:
        form = StaffUserForm()

    return render(request, 'wardens/warden_form.html', {'form': form, 'title': 'Add New Warden'})


@login_required
@admin_required
def warden_edit(request, pk):
    """Admin view to edit warden permissions and block assignment."""
    warden = get_object_or_404(User, pk=pk, role=User.Role.WARDEN)
    if request.method == 'POST':
        form = StaffUserForm(request.POST, request.FILES, instance=warden)
        if form.is_valid():
            form.save()
            messages.success(request, f"Warden {warden.get_full_name() or warden.username} updated successfully.")
            return redirect('warden_list')
    else:
        form = StaffUserForm(instance=warden)

    return render(request, 'wardens/warden_form.html', {'form': form, 'title': f'Edit Warden: {warden.username}'})


# ==========================================
# ANNOUNCEMENTS MANAGEMENT
# ==========================================

@login_required
def announcement_list(request):
    """View active hostel announcements and notice board."""
    announcements = HostelAnnouncement.objects.select_related('published_by').order_by('-created_at')
    return render(request, 'announcements/announcement_list.html', {'announcements': announcements})


@login_required
@warden_or_admin_required
def announcement_create(request):
    """Publish a new hostel notice / announcement."""
    if request.method == 'POST':
        form = HostelAnnouncementForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.published_by = request.user
            notice.save()

            # Broadcast notification to active student residents
            active_students = User.objects.filter(role=User.Role.STUDENT, allotments__is_active=True).distinct()
            notifications_to_create = [
                Notification(
                    recipient=s,
                    title=f"Hostel Notice: {notice.title}",
                    message=notice.content[:200],
                    notification_type=Notification.Type.ANNOUNCEMENT,
                    link_url='/announcements/'
                )
                for s in active_students
            ]
            Notification.objects.bulk_create(notifications_to_create)

            messages.success(request, f"Announcement '{notice.title}' published successfully!")
            return redirect('announcement_list')
    else:
        form = HostelAnnouncementForm()

    return render(request, 'announcements/announcement_form.html', {'form': form})


@login_required
@admin_required
def announcement_delete(request, pk):
    """Delete an announcement."""
    notice = get_object_or_404(HostelAnnouncement, pk=pk)
    notice.delete()
    messages.info(request, "Announcement removed.")
    return redirect('announcement_list')


# ==========================================
# FEE MANAGEMENT & VOUCHERS
# ==========================================

@login_required
def fee_voucher_list(request):
    """Fee Vouchers List (Filtered by role: student sees own, warden sees assigned block, admin sees all)."""
    user = request.user
    status_filter = request.GET.get('status', '')
    fee_type_filter = request.GET.get('fee_type', '')

    if user.is_student_user:
        vouchers = user.fee_vouchers.all()
    elif user.is_warden_user and user.assigned_block:
        vouchers = FeeVoucher.objects.filter(
            student__allotments__room__block=user.assigned_block,
            student__allotments__is_active=True
        ).distinct().select_related('student', 'verified_by')
    else:
        vouchers = FeeVoucher.objects.select_related('student', 'verified_by')

    if status_filter:
        vouchers = vouchers.filter(status=status_filter)
    if fee_type_filter:
        vouchers = vouchers.filter(fee_type=fee_type_filter)

    vouchers = vouchers.order_by('-due_date', '-created_at')

    paginator = Paginator(vouchers, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'fee_type_filter': fee_type_filter,
        'status_choices': FeeVoucher.Status.choices,
        'fee_type_choices': FeeVoucher.FeeType.choices,
    }
    return render(request, 'fees/voucher_list.html', context)


@login_required
@student_required
def student_fee_upload(request):
    """
    Dedicated Fee Voucher Upload view for students:
    Allows students to upload their hostel fee vouchers (PDF, JPG, PNG).
    Submits voucher for administrative verification.
    """
    student = request.user
    if request.method == 'POST':
        form = StudentFeeVoucherUploadForm(request.POST, request.FILES)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.student = student
            voucher.status = FeeVoucher.Status.PENDING_VERIFICATION
            if not voucher.due_date:
                voucher.due_date = timezone.now().date()
            voucher.save()

            # Send in-app notification to student
            Notification.send(
                recipient=student,
                title="Fee Voucher Submitted",
                message=f"Your fee voucher #{voucher.voucher_code} (Rs. {voucher.amount}) for {voucher.billing_month} has been uploaded and is pending administrative verification.",
                notification_type=Notification.Type.GENERAL,
                link_url=f"/fees/{voucher.pk}/voucher/"
            )

            # Send in-app notification to administrators
            admin_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.CHIEF_WARDEN])
            for admin_u in admin_users:
                Notification.send(
                    recipient=admin_u,
                    title="New Fee Voucher Uploaded",
                    message=f"Student {student.get_full_name() or student.username} ({student.registration_no or student.cnic}) uploaded fee voucher #{voucher.voucher_code} of Rs. {voucher.amount} for verification.",
                    notification_type=Notification.Type.GENERAL,
                    link_url=f"/fees/{voucher.pk}/verify/"
                )

            messages.success(request, f"Fee voucher #{voucher.voucher_code} uploaded successfully! Our administration will review and verify your payment.")
            return redirect('student_portal')
        else:
            messages.error(request, "Failed to upload fee voucher. Please check the form errors and ensure your file is in PDF, JPG, or PNG format.")
    else:
        form = StudentFeeVoucherUploadForm()

    return render(request, 'fees/upload_voucher.html', {'form': form})


@login_required
@warden_or_admin_required
def fee_voucher_create(request):
    """Generate individual fee voucher."""
    if request.method == 'POST':
        form = FeeVoucherCreateForm(request.POST)
        if form.is_valid():
            voucher = form.save()
            Notification.send(
                recipient=voucher.student,
                title="New Fee Voucher Generated",
                message=f"Fee Voucher #{voucher.voucher_code} of Rs. {voucher.amount} for {voucher.billing_month} generated. Due date: {voucher.due_date}.",
                notification_type=Notification.Type.GENERAL,
                link_url=f"/fees/{voucher.pk}/pay/"
            )
            messages.success(request, f"Fee Voucher {voucher.voucher_code} generated for {voucher.student.username}.")
            return redirect('fee_voucher_list')
    else:
        form = FeeVoucherCreateForm()

    return render(request, 'fees/voucher_form.html', {'form': form})


@login_required
@warden_or_admin_required
def bulk_fee_generate(request):
    """Generate fee invoices for all currently active hostel residents."""
    if request.method == 'POST':
        form = BulkFeeGenerateForm(request.POST)
        if form.is_valid():
            fee_type = form.cleaned_data['fee_type']
            billing_month = form.cleaned_data['billing_month']
            amount = form.cleaned_data['amount']
            due_date = form.cleaned_data['due_date']
            remarks = form.cleaned_data['remarks']

            active_allotments = Allotment.objects.filter(is_active=True).select_related('student')
            created_count = 0

            with transaction.atomic():
                for allotment in active_allotments:
                    v = FeeVoucher.objects.create(
                        student=allotment.student,
                        fee_type=fee_type,
                        billing_month=billing_month,
                        amount=amount,
                        due_date=due_date,
                        remarks=remarks
                    )
                    Notification.send(
                        recipient=allotment.student,
                        title=f"Monthly Fee Voucher ({billing_month})",
                        message=f"Monthly hostel fee voucher #{v.voucher_code} (Rs. {amount}) generated. Due: {due_date}.",
                        notification_type=Notification.Type.GENERAL,
                        link_url=f"/fees/{v.pk}/pay/"
                    )
                    created_count += 1

            messages.success(request, f"Successfully created {created_count} fee vouchers for active residents.")
            return redirect('fee_voucher_list')
    else:
        form = BulkFeeGenerateForm()

    return render(request, 'fees/bulk_voucher_form.html', {'form': form})


@login_required
def fee_submit_payment(request, pk):
    """Student uploads payment receipt and transaction ID."""
    voucher = get_object_or_404(FeeVoucher, pk=pk)

    if request.user.is_student_user and voucher.student != request.user:
        messages.error(request, "Unauthorized access to this fee voucher.")
        return redirect('fee_voucher_list')

    if request.method == 'POST':
        form = FeePaymentProofForm(request.POST, request.FILES, instance=voucher)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.status = FeeVoucher.Status.PENDING_VERIFICATION
            voucher.save()
            messages.success(request, f"Payment proof for {voucher.voucher_code} submitted! Pending staff verification.")
            return redirect('fee_voucher_list')
    else:
        form = FeePaymentProofForm(instance=voucher)

    return render(request, 'fees/submit_payment.html', {'voucher': voucher, 'form': form})


@login_required
@warden_or_admin_required
def fee_verify(request, pk):
    """Warden / Admin reviews payment proof and marks voucher as PAID, PENDING, or REJECTED."""
    voucher = get_object_or_404(FeeVoucher.objects.select_related('student'), pk=pk)

    if request.method == 'POST':
        form = FeeVerificationForm(request.POST, instance=voucher)
        if form.is_valid():
            voucher = form.save(commit=False)
            if voucher.status in [FeeVoucher.Status.PAID, FeeVoucher.Status.REJECTED]:
                voucher.verified_by = request.user
                voucher.verified_at = timezone.now()
            voucher.save()

            status_display = voucher.get_status_display()
            remarks_text = f" Remarks: {voucher.remarks}" if voucher.remarks else ""
            Notification.send(
                recipient=voucher.student,
                title=f"Fee Payment {status_display}",
                message=f"Your payment for voucher #{voucher.voucher_code} has been marked as {status_display}.{remarks_text}",
                notification_type=Notification.Type.GENERAL,
                link_url=f"/fees/{voucher.pk}/voucher/"
            )

            messages.success(request, f"Fee voucher {voucher.voucher_code} verification updated to: {status_display}.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('fee_voucher_list')
        else:
            messages.error(request, "Please check the verification form for errors.")
    else:
        form = FeeVerificationForm(instance=voucher)

    return render(request, 'fees/verify_payment.html', {'voucher': voucher, 'form': form})


@login_required
def fee_voucher_detail(request, pk):
    """Printable invoice / voucher view with role-based access control."""
    voucher = get_object_or_404(FeeVoucher.objects.select_related('student', 'verified_by'), pk=pk)

    # Privacy check: Students can only view their own voucher
    if request.user.is_student_user and voucher.student != request.user:
        messages.error(request, "Unauthorized access. You can only view your own fee vouchers.")
        return redirect('student_portal')

    # Wardens can only view students in their assigned block
    if request.user.is_warden_user and request.user.assigned_block:
        student_in_block = voucher.student.allotments.filter(
            room__block=request.user.assigned_block,
            is_active=True
        ).exists()
        if not student_in_block:
            messages.error(request, "Unauthorized access. Student does not belong to your assigned block.")
            return redirect('warden_portal')

    return render(request, 'fees/voucher_detail.html', {'voucher': voucher})


# ==========================================
# GATE PASS / LEAVE REQUESTS
# ==========================================

@login_required
def gate_pass_list(request):
    """Gate pass requests list."""
    status_filter = request.GET.get('status', '')

    if request.user.is_student_user:
        gate_passes = request.user.gate_passes.all()
    else:
        gate_passes = GatePass.objects.select_related('student', 'approved_by')

    if status_filter:
        gate_passes = gate_passes.filter(status=status_filter)

    gate_passes = gate_passes.order_by('-created_at')

    paginator = Paginator(gate_passes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': GatePass.Status.choices,
    }
    return render(request, 'gatepasses/gatepass_list.html', context)


@login_required
@student_required
def gate_pass_request(request):
    """Student requests leave/gate pass."""
    if request.method == 'POST':
        form = GatePassRequestForm(request.POST)
        if form.is_valid():
            pass_obj = form.save(commit=False)
            pass_obj.student = request.user
            pass_obj.save()
            messages.success(request, f"Gate Pass request #{pass_obj.pass_code} submitted. Awaiting warden review.")
            return redirect('gate_pass_list')
    else:
        initial_data = {}
        if request.user.emergency_contact:
            initial_data['emergency_contact'] = request.user.emergency_contact
        form = GatePassRequestForm(initial=initial_data)

    return render(request, 'gatepasses/gatepass_form.html', {'form': form})


@login_required
@warden_or_admin_required
def gate_pass_action(request, pk, action):
    """Quick Approve or Reject gate pass by warden."""
    gate_pass = get_object_or_404(GatePass, pk=pk)

    if action == 'approve':
        gate_pass.status = GatePass.Status.APPROVED
        gate_pass.approved_by = request.user
        gate_pass.save()
        Notification.send(
            recipient=gate_pass.student,
            title="Gate Pass Approved",
            message=f"Your gate pass #{gate_pass.pass_code} to {gate_pass.destination} has been APPROVED.",
            notification_type=Notification.Type.GENERAL,
            link_url='/gatepasses/'
        )
        messages.success(request, f"Gate Pass {gate_pass.pass_code} for {gate_pass.student.username} has been APPROVED.")
    elif action == 'reject':
        rejection_reason = request.POST.get('rejection_reason', 'Disapproved by hostel warden.')
        gate_pass.status = GatePass.Status.REJECTED
        gate_pass.approved_by = request.user
        gate_pass.rejection_reason = rejection_reason
        gate_pass.save()
        Notification.send(
            recipient=gate_pass.student,
            title="Gate Pass Rejected",
            message=f"Your gate pass #{gate_pass.pass_code} was REJECTED: {rejection_reason}",
            notification_type=Notification.Type.GENERAL,
            link_url='/gatepasses/'
        )
        messages.warning(request, f"Gate Pass {gate_pass.pass_code} has been REJECTED.")

    next_url = request.POST.get('next', request.GET.get('next', 'gate_pass_list'))
    return redirect(next_url)


# ==========================================
# MESS TIMETABLE
# ==========================================

@login_required
def mess_menu_view(request):
    """Display the full 7-day mess timetable."""
    days = MessSchedule.DayOfWeek.choices
    meal_types = MessSchedule.MealType.choices

    schedule_items = MessSchedule.objects.all()
    menu_matrix = {day[0]: {} for day in days}
    for item in schedule_items:
        menu_matrix[item.day_of_week][item.meal_type] = item

    current_day = timezone.now().strftime('%A').upper()

    context = {
        'days': days,
        'meal_types': meal_types,
        'menu_matrix': menu_matrix,
        'current_day': current_day,
    }
    return render(request, 'mess/mess_menu.html', context)


@login_required
@warden_or_admin_required
def mess_menu_edit(request):
    """Add or edit mess menu item."""
    item_id = request.GET.get('id')
    instance = get_object_or_404(MessSchedule, pk=item_id) if item_id else None

    if request.method == 'POST':
        form = MessScheduleForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Mess timetable schedule updated successfully.")
            return redirect('mess_menu')
    else:
        form = MessScheduleForm(instance=instance)

    return render(request, 'mess/mess_form.html', {'form': form, 'instance': instance})


# ==========================================
# REPORTING & CSV EXPORT
# ==========================================

@login_required
@warden_or_admin_required
def export_students_csv(request):
    """Export resident students directory to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="hostel_students_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student ID / Roll No', 'Username', 'Full Name', 'Department', 'Semester',
        'Email', 'Phone', 'Gender', 'Emergency Contact', 'Hostel', 'Block', 'Room', 'Bed', 'Allotment Date'
    ])

    active_allotments = Allotment.objects.filter(is_active=True).select_related(
        'student', 'room', 'bed', 'room__block', 'room__block__hostel'
    )

    for a in active_allotments:
        writer.writerow([
            a.student.registration_no or a.student.cnic_or_id,
            a.student.username,
            a.student.get_full_name(),
            a.student.department,
            a.student.semester,
            a.student.email,
            a.student.phone_number,
            a.student.get_gender_display(),
            a.student.emergency_contact,
            a.room.block.hostel.name,
            a.room.block.block_name,
            a.room.room_number,
            a.bed.bed_code,
            a.allotment_date.strftime('%Y-%m-%d'),
        ])

    return response


@login_required
@warden_or_admin_required
def export_fee_defaulters_csv(request):
    """Export Fee Defaulters List to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="fee_defaulters_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Voucher Code', 'Student Name', 'Username', 'Phone Number',
        'Fee Type', 'Billing Month', 'Amount Due', 'Due Date', 'Status'
    ])

    defaulters = FeeVoucher.objects.filter(
        status__in=[FeeVoucher.Status.UNPAID, FeeVoucher.Status.OVERDUE],
        due_date__lt=timezone.now().date()
    ).select_related('student')

    for v in defaulters:
        writer.writerow([
            v.voucher_code,
            v.student.get_full_name(),
            v.student.username,
            v.student.phone_number,
            v.get_fee_type_display(),
            v.billing_month,
            v.amount,
            v.due_date.strftime('%Y-%m-%d'),
            v.get_status_display()
        ])

    return response


@login_required
@warden_or_admin_required
def export_room_inventory_csv(request):
    """Export room-wise inventory with full resident details to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ali_hall_rooms_roster_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Room #', 'Floor', 'Wing / Block', 'Reservation Quota', 'Room Status',
        'Bed Code', 'Bed Status', 'Resident Name', 'Username', 'Mobile Number',
        'CNIC', 'Address / City', 'Department', 'Semester', 'Registration #', 'Emergency Contact'
    ])

    rooms = Room.objects.select_related('block').prefetch_related('beds__allotments__student').annotate(
        r_num_int=Cast('room_number', output_field=IntegerField())
    ).order_by('floor', 'r_num_int')

    for r in rooms:
        quota_label = "Special Students (Ground Floor)" if r.is_special_reserved else "Regular Students"
        for bed in r.beds.all():
            student = bed.current_student
            if student:
                writer.writerow([
                    r.room_number,
                    f"Floor {r.floor}",
                    r.block.block_name,
                    quota_label,
                    r.occupancy_status_display,
                    bed.bed_code,
                    bed.get_status_display(),
                    student.get_full_name() or student.username,
                    student.username,
                    student.phone_number or 'N/A',
                    student.cnic_or_id or 'N/A',
                    student.address or 'N/A',
                    student.department or 'N/A',
                    f"Semester {student.semester}" if student.semester else 'N/A',
                    student.registration_no or 'N/A',
                    student.emergency_contact or 'N/A'
                ])
            else:
                writer.writerow([
                    r.room_number,
                    f"Floor {r.floor}",
                    r.block.block_name,
                    quota_label,
                    r.occupancy_status_display,
                    bed.bed_code,
                    bed.get_status_display(),
                    'VACANT',
                    'VACANT',
                    'N/A',
                    'N/A',
                    'N/A',
                    'N/A',
                    'N/A',
                    'N/A',
                    'N/A'
                ])

    return response
