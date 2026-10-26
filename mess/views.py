import csv
import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    StudentProfile, MealMenu, MealAttendance, MessFee, FeePayment, MessExpense, Announcement
)
from .forms import (
    StudentProfileForm, StudentSelfProfileForm, MealMenuForm,
    BulkMessFeeGenerateForm, FeePaymentForm, MessExpenseForm, AnnouncementForm
)

User = get_user_model()


def is_mess_admin(user):
    """Check if user is administrator or staff."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or getattr(user, 'role', '') in ['ADMIN', 'WARDEN']


# ==========================================
# DASHBOARD
# ==========================================

@login_required
def mess_dashboard_router(request):
    """
    Intelligent router directing administrators to admin mess dashboard
    and students to their personal mess portal.
    """
    if is_mess_admin(request.user):
        return admin_mess_dashboard(request)
    else:
        return student_mess_portal(request)


@login_required
def admin_mess_dashboard(request):
    """
    Executive Hostel Mess Management Dashboard with statistics, today's menus,
    financial charts, attendance breakdown, and recent activity.
    """
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    today = timezone.now().date()
    current_month_str = today.strftime('%B %Y')

    # 1. Student Statistics
    total_students = StudentProfile.objects.count()
    active_mess_members = StudentProfile.objects.filter(is_active=True, mess_status=StudentProfile.MessStatus.ACTIVE).count()
    inactive_members = StudentProfile.objects.filter(Q(is_active=False) | Q(mess_status=StudentProfile.MessStatus.INACTIVE)).count()

    # 2. Today's Menus
    today_menus = MealMenu.objects.filter(date=today).order_by('meal_type')
    breakfast_menu = today_menus.filter(meal_type=MealMenu.MealType.BREAKFAST).first()
    lunch_menu = today_menus.filter(meal_type=MealMenu.MealType.LUNCH).first()
    evening_tea_menu = today_menus.filter(meal_type=MealMenu.MealType.EVENING_TEA).first()
    dinner_menu = today_menus.filter(meal_type=MealMenu.MealType.DINNER).first()

    # 3. Monthly Financial Metrics
    current_month_fees = MessFee.objects.filter(month_date__year=today.year, month_date__month=today.month)
    total_billed = current_month_fees.aggregate(total=Sum('total_fee'))['total'] or 0
    total_collected = current_month_fees.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_pending = total_billed - total_collected

    # 4. Monthly Expenses
    current_month_expenses = MessExpense.objects.filter(expense_date__year=today.year, expense_date__month=today.month)
    total_expenses = current_month_expenses.aggregate(total=Sum('amount'))['total'] or 0

    # 5. Today's Attendance Counts
    today_attendances = MealAttendance.objects.filter(date=today, status=MealAttendance.AttendanceStatus.PRESENT)
    attendance_breakfast = today_attendances.filter(meal_type=MealMenu.MealType.BREAKFAST).count()
    attendance_lunch = today_attendances.filter(meal_type=MealMenu.MealType.LUNCH).count()
    attendance_dinner = today_attendances.filter(meal_type=MealMenu.MealType.DINNER).count()

    # 6. Recent Registrations & Announcements
    recent_students = StudentProfile.objects.order_by('-created_at')[:5]
    latest_announcements = Announcement.objects.filter(is_active=True).order_by('-published_date')[:4]

    # 7. Chart Data: Monthly Income vs Expenses (Last 6 Months)
    chart_months = []
    chart_income = []
    chart_expense = []

    for i in range(5, -1, -1):
        m_date = today.replace(day=1) - timedelta(days=i * 28)
        m_label = m_date.strftime('%b %Y')
        chart_months.append(m_label)

        inc = FeePayment.objects.filter(payment_date__year=m_date.year, payment_date__month=m_date.month).aggregate(t=Sum('amount'))['t'] or 0
        exp = MessExpense.objects.filter(expense_date__year=m_date.year, expense_date__month=m_date.month).aggregate(t=Sum('amount'))['t'] or 0
        chart_income.append(float(inc))
        chart_expense.append(float(exp))

    context = {
        'today': today,
        'current_month_str': current_month_str,
        'total_students': total_students,
        'active_mess_members': active_mess_members,
        'inactive_members': inactive_members,
        'breakfast_menu': breakfast_menu,
        'lunch_menu': lunch_menu,
        'evening_tea_menu': evening_tea_menu,
        'dinner_menu': dinner_menu,
        'total_billed': total_billed,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_expenses': total_expenses,
        'attendance_breakfast': attendance_breakfast,
        'attendance_lunch': attendance_lunch,
        'attendance_dinner': attendance_dinner,
        'recent_students': recent_students,
        'latest_announcements': latest_announcements,
        'chart_months_json': json.dumps(chart_months),
        'chart_income_json': json.dumps(chart_income),
        'chart_expense_json': json.dumps(chart_expense),
    }
    return render(request, 'mess/admin_dashboard.html', context)


@login_required
def student_mess_portal(request):
    """
    Dedicated Student Portal Dashboard:
    Profile summary, today's menus, attendance records, fee dues, announcements.
    """
    # Link student profile to current user if exists
    profile = getattr(request.user, 'student_profile', None)
    if not profile:
        # Fallback search by username
        profile = StudentProfile.objects.filter(Q(student_id__iexact=request.user.username) | Q(email__iexact=request.user.email)).first()

    today = timezone.now().date()
    today_menus = MealMenu.objects.filter(date=today).order_by('meal_type')

    # Personal Attendance (Last 10 records)
    my_attendances = []
    my_fees = []
    my_total_pending = 0

    if profile:
        my_attendances = profile.meal_attendances.order_by('-date')[:8]
        my_fees = profile.mess_fees.order_by('-month_date')[:6]
        my_total_pending = profile.total_outstanding_balance

    latest_announcements = Announcement.objects.filter(is_active=True).order_by('-published_date')[:5]

    context = {
        'profile': profile,
        'today': today,
        'today_menus': today_menus,
        'my_attendances': my_attendances,
        'my_fees': my_fees,
        'my_total_pending': my_total_pending,
        'latest_announcements': latest_announcements,
    }
    return render(request, 'mess/student_portal.html', context)


# ==========================================
# STUDENT MANAGEMENT
# ==========================================

@login_required
def student_list_view(request):
    """Filterable and searchable Student Directory."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    search_query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    sem_filter = request.GET.get('semester', '').strip()
    status_filter = request.GET.get('status', '').strip()

    students = StudentProfile.objects.all().order_by('student_id')

    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(hostel_room_no__icontains=search_query)
        )

    if dept_filter:
        students = students.filter(department__icontains=dept_filter)
    if sem_filter:
        students = students.filter(semester=sem_filter)
    if status_filter:
        students = students.filter(mess_status=status_filter)

    departments = StudentProfile.objects.values_list('department', flat=True).distinct().order_by('department')

    context = {
        'students': students,
        'search_query': search_query,
        'dept_filter': dept_filter,
        'sem_filter': sem_filter,
        'status_filter': status_filter,
        'departments': departments,
        'semester_choices': StudentProfile.Semester.choices,
        'status_choices': StudentProfile.MessStatus.choices,
    }
    return render(request, 'mess/student_list.html', context)


@login_required
def student_create_view(request):
    """Add a new student with profile photo upload and optional portal user account."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                student = form.save()
                # Create user account for login if checked
                if form.cleaned_data.get('create_user_account'):
                    username = student.student_id.strip().lower()
                    if not User.objects.filter(username=username).exists():
                        user = User.objects.create_user(
                            username=username,
                            email=student.email,
                            first_name=student.full_name.split()[0] if student.full_name else '',
                            last_name=" ".join(student.full_name.split()[1:]) if len(student.full_name.split()) > 1 else '',
                            password='student123'
                        )
                        if hasattr(user, 'role'):
                            user.role = 'STUDENT'
                            user.save()
                        student.user = user
                        student.save()

            messages.success(request, f"Student {student.full_name} ({student.student_id}) enrolled successfully!")
            return redirect('student_detail', pk=student.pk)
        else:
            messages.error(request, "Please fix the validation errors below.")
    else:
        form = StudentProfileForm()

    return render(request, 'mess/student_form.html', {'form': form, 'title': 'Add New Mess Student'})


@login_required
def student_detail_view(request, pk):
    """Detailed Student Profile with fee ledger, attendance history, and payment records."""
    if not is_mess_admin(request.user):
        # A student can only view their own profile
        profile = getattr(request.user, 'student_profile', None)
        if not profile or profile.pk != pk:
            messages.error(request, "Unauthorized access to other student records.")
            return redirect('student_mess_portal')

    student = get_object_or_404(StudentProfile, pk=pk)
    fees = student.mess_fees.order_by('-month_date')
    payments = student.payments.order_by('-payment_date')
    attendances = student.meal_attendances.order_by('-date')[:15]

    total_present = student.meal_attendances.filter(status=MealAttendance.AttendanceStatus.PRESENT).count()
    total_absent = student.meal_attendances.filter(status=MealAttendance.AttendanceStatus.ABSENT).count()

    context = {
        'student': student,
        'fees': fees,
        'payments': payments,
        'attendances': attendances,
        'total_present': total_present,
        'total_absent': total_absent,
    }
    return render(request, 'mess/student_detail.html', context)


@login_required
def student_edit_view(request, pk):
    """Edit student information and change photo."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student profile for {student.full_name} updated successfully.")
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'mess/student_form.html', {
        'form': form,
        'student': student,
        'title': f'Edit Student: {student.full_name}'
    })


@login_required
def student_delete_view(request, pk):
    """Delete student with confirmation."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        roll = student.student_id
        student.delete()
        messages.success(request, f"Student record {name} ({roll}) has been deleted.")
        return redirect('student_list')

    return render(request, 'mess/student_confirm_delete.html', {'student': student})


@login_required
def student_profile_self_edit(request):
    """Student portal: update personal photo and contact information."""
    profile = getattr(request.user, 'student_profile', None)
    if not profile:
        profile = StudentProfile.objects.filter(Q(student_id__iexact=request.user.username) | Q(email__iexact=request.user.email)).first()

    if not profile:
        messages.error(request, "Student profile not found. Please contact the mess manager.")
        return redirect('student_mess_portal')

    if request.method == 'POST':
        form = StudentSelfProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('student_mess_portal')
    else:
        form = StudentSelfProfileForm(instance=profile)

    return render(request, 'mess/student_self_edit.html', {'form': form, 'profile': profile})


# ==========================================
# DAILY & WEEKLY MENU MANAGEMENT
# ==========================================

@login_required
def menu_weekly_view(request):
    """
    Weekly Menu Matrix (Monday - Sunday) with Breakfast, Lunch, Evening Tea, Dinner.
    """
    days = MealMenu.DayOfWeek.choices
    meal_types = MealMenu.MealType.choices

    day_filter = request.GET.get('day', '')
    meal_filter = request.GET.get('meal_type', '')

    today = timezone.now().date()
    current_day_name = today.strftime('%A').upper()

    menus = MealMenu.objects.all().order_by('date')
    if day_filter:
        menus = menus.filter(day_of_week=day_filter)
    if meal_filter:
        menus = menus.filter(meal_type=meal_filter)

    # Build weekly schedule dictionary: {DAY: {MEAL_TYPE: menu_object}}
    weekly_grid = {day[0]: {} for day in days}
    for m in menus:
        weekly_grid[m.day_of_week][m.meal_type] = m

    context = {
        'days': days,
        'meal_types': meal_types,
        'weekly_grid': weekly_grid,
        'today': today,
        'current_day_name': current_day_name,
        'day_filter': day_filter,
        'meal_filter': meal_filter,
    }
    return render(request, 'mess/menu_weekly.html', context)


@login_required
def menu_create_view(request):
    """Create a new daily/weekly meal menu item with optional dish image."""
    if not is_mess_admin(request.user):
        return redirect('menu_weekly')

    if request.method == 'POST':
        form = MealMenuForm(request.POST, request.FILES)
        if form.is_valid():
            menu = form.save()
            messages.success(request, f"{menu.get_meal_type_display()} menu for {menu.date} scheduled successfully.")
            return redirect('menu_weekly')
    else:
        initial = {'date': timezone.now().date()}
        form = MealMenuForm(initial=initial)

    return render(request, 'mess/menu_form.html', {'form': form, 'title': 'Create Meal Menu'})


@login_required
def menu_edit_view(request, pk):
    """Edit meal menu item."""
    if not is_mess_admin(request.user):
        return redirect('menu_weekly')

    menu = get_object_or_404(MealMenu, pk=pk)
    if request.method == 'POST':
        form = MealMenuForm(request.POST, request.FILES, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, f"{menu.get_meal_type_display()} menu for {menu.date} updated.")
            return redirect('menu_weekly')
    else:
        form = MealMenuForm(instance=menu)

    return render(request, 'mess/menu_form.html', {'form': form, 'menu': menu, 'title': 'Edit Meal Menu'})


@login_required
def menu_delete_view(request, pk):
    """Delete a meal menu item."""
    if not is_mess_admin(request.user):
        return redirect('menu_weekly')

    menu = get_object_or_404(MealMenu, pk=pk)
    if request.method == 'POST':
        menu.delete()
        messages.success(request, "Meal menu item has been removed.")
        return redirect('menu_weekly')

    return render(request, 'mess/menu_confirm_delete.html', {'menu': menu})


# ==========================================
# MESS ATTENDANCE
# ==========================================

@login_required
def attendance_mark_view(request):
    """
    Mark student attendance for Breakfast, Lunch, or Dinner with zero duplicate protection.
    """
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    selected_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    selected_meal = request.GET.get('meal_type', MealMenu.MealType.LUNCH)

    try:
        selected_date = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    active_students = StudentProfile.objects.filter(is_active=True, mess_status=StudentProfile.MessStatus.ACTIVE).order_by('student_id')

    if request.method == 'POST':
        present_ids = request.POST.getlist('present_students')
        remarks_dict = {key.split('_')[1]: val for key, val in request.POST.items() if key.startswith('remark_')}

        with transaction.atomic():
            for student in active_students:
                status = MealAttendance.AttendanceStatus.PRESENT if str(student.id) in present_ids else MealAttendance.AttendanceStatus.ABSENT
                remark = remarks_dict.get(str(student.id), '')

                MealAttendance.objects.update_or_create(
                    student=student,
                    date=selected_date,
                    meal_type=selected_meal,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'remarks': remark
                    }
                )

        messages.success(request, f"Attendance for {selected_meal.title()} on {selected_date} marked successfully!")
        return redirect(f"{request.path}?date={selected_date}&meal_type={selected_meal}")

    # Load existing attendance records for the selected date & meal
    existing_attendance = {
        att.student_id: att for att in MealAttendance.objects.filter(date=selected_date, meal_type=selected_meal)
    }

    # Prepare list with status
    attendance_data = []
    for s in active_students:
        att = existing_attendance.get(s.id)
        attendance_data.append({
            'student': s,
            'is_present': att.status == MealAttendance.AttendanceStatus.PRESENT if att else False,
            'remark': att.remarks if att else '',
        })

    total_present_count = sum(1 for item in attendance_data if item['is_present'])

    context = {
        'selected_date': selected_date,
        'selected_meal': selected_meal,
        'attendance_data': attendance_data,
        'total_present_count': total_present_count,
        'total_students_count': len(active_students),
        'meal_types': MealMenu.MealType.choices,
    }
    return render(request, 'mess/attendance_mark.html', context)


@login_required
def attendance_report_view(request):
    """
    Daily & Monthly attendance reports with filters.
    """
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    month_filter = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    meal_filter = request.GET.get('meal_type', '')

    year, month = map(int, month_filter.split('-'))

    attendances = MealAttendance.objects.filter(date__year=year, date__month=month).select_related('student')
    if meal_filter:
        attendances = attendances.filter(meal_type=meal_filter)

    total_records = attendances.count()
    total_presents = attendances.filter(status=MealAttendance.AttendanceStatus.PRESENT).count()
    total_absents = attendances.filter(status=MealAttendance.AttendanceStatus.ABSENT).count()

    context = {
        'attendances': attendances[:100],  # Show recent 100
        'month_filter': month_filter,
        'meal_filter': meal_filter,
        'total_records': total_records,
        'total_presents': total_presents,
        'total_absents': total_absents,
        'meal_types': MealMenu.MealType.choices,
    }
    return render(request, 'mess/attendance_report.html', context)


# ==========================================
# MESS FEES & EXPENSES
# ==========================================

@login_required
def fee_list_view(request):
    """Mess Fee Invoices list."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    status_filter = request.GET.get('status', '')
    month_filter = request.GET.get('month', '')
    search_query = request.GET.get('q', '').strip()

    fees = MessFee.objects.select_related('student').order_by('-month_date', 'student__student_id')

    if status_filter:
        fees = fees.filter(status=status_filter)
    if month_filter:
        fees = fees.filter(billing_month__icontains=month_filter)
    if search_query:
        fees = fees.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__full_name__icontains=search_query)
        )

    # Financial totals
    total_billed = fees.aggregate(t=Sum('total_fee'))['t'] or 0
    total_paid = fees.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_pending = total_billed - total_paid

    context = {
        'fees': fees,
        'status_filter': status_filter,
        'month_filter': month_filter,
        'search_query': search_query,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'status_choices': MessFee.FeeStatus.choices,
    }
    return render(request, 'mess/fee_list.html', context)


@login_required
def fee_bulk_generate_view(request):
    """Bulk generate monthly fee invoices for all active residents."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    if request.method == 'POST':
        form = BulkMessFeeGenerateForm(request.POST)
        if form.is_valid():
            billing_month = form.cleaned_data['billing_month']
            month_date = form.cleaned_data['month_date']
            total_fee = form.cleaned_data['total_fee']
            due_date = form.cleaned_data['due_date']
            remarks = form.cleaned_data['remarks']

            active_students = StudentProfile.objects.filter(is_active=True, mess_status=StudentProfile.MessStatus.ACTIVE)
            count = 0

            with transaction.atomic():
                for s in active_students:
                    # Skip if already exists
                    if not MessFee.objects.filter(student=s, billing_month=billing_month).exists():
                        MessFee.objects.create(
                            student=s,
                            billing_month=billing_month,
                            month_date=month_date,
                            total_fee=s.monthly_mess_fee or total_fee,
                            due_date=due_date,
                            remarks=remarks
                        )
                        count += 1

            messages.success(request, f"Generated {count} mess fee invoices for {billing_month}!")
            return redirect('fee_list')
    else:
        form = BulkMessFeeGenerateForm(initial={
            'billing_month': timezone.now().strftime('%B %Y'),
            'due_date': timezone.now().date() + timedelta(days=10)
        })

    return render(request, 'mess/fee_bulk_form.html', {'form': form})


@login_required
def fee_payment_create_view(request, fee_id=None):
    """Record a cash/bank payment for an invoice."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    initial_fee = None
    if fee_id:
        initial_fee = get_object_or_404(MessFee, pk=fee_id)

    if request.method == 'POST':
        form = FeePaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.student = payment.mess_fee.student
            payment.received_by = request.user
            payment.save()
            messages.success(request, f"Payment of Rs. {payment.amount} recorded for {payment.student.full_name}!")
            return redirect('fee_list')
    else:
        initial_data = {}
        if initial_fee:
            initial_data = {
                'mess_fee': initial_fee,
                'amount': initial_fee.remaining_balance,
                'payment_date': timezone.now().date()
            }
        form = FeePaymentForm(initial=initial_data)

    return render(request, 'mess/fee_payment_form.html', {'form': form, 'initial_fee': initial_fee})


@login_required
def expense_list_view(request):
    """Mess Operating Expenses list & recording desk."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    category_filter = request.GET.get('category', '')
    month_filter = request.GET.get('month', '')

    expenses = MessExpense.objects.select_related('recorded_by').order_by('-expense_date')

    if category_filter:
        expenses = expenses.filter(category=category_filter)
    if month_filter:
        try:
            y, m = map(int, month_filter.split('-'))
            expenses = expenses.filter(expense_date__year=y, expense_date__month=m)
        except ValueError:
            pass

    total_expense_amount = expenses.aggregate(t=Sum('amount'))['t'] or 0

    # Add Expense Form modal/handler
    if request.method == 'POST':
        form = MessExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.recorded_by = request.user
            exp.save()
            messages.success(request, f"Expense '{exp.title}' of Rs. {exp.amount} recorded.")
            return redirect('expense_list')
    else:
        form = MessExpenseForm(initial={'expense_date': timezone.now().date()})

    context = {
        'expenses': expenses,
        'form': form,
        'category_filter': category_filter,
        'month_filter': month_filter,
        'total_expense_amount': total_expense_amount,
        'categories': MessExpense.Category.choices,
    }
    return render(request, 'mess/expense_list.html', context)


@login_required
def expense_report_view(request):
    """Monthly Income vs Expense Financial Report."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    today = timezone.now().date()
    month_filter = request.GET.get('month', today.strftime('%Y-%m'))
    year, month = map(int, month_filter.split('-'))

    # Income
    payments = FeePayment.objects.filter(payment_date__year=year, payment_date__month=month)
    total_income = payments.aggregate(t=Sum('amount'))['t'] or 0

    # Expenses
    expenses = MessExpense.objects.filter(expense_date__year=year, expense_date__month=month)
    total_expense = expenses.aggregate(t=Sum('amount'))['t'] or 0

    # Categorized expenses breakdown
    food_exp = expenses.filter(category=MessExpense.Category.FOOD).aggregate(t=Sum('amount'))['t'] or 0
    grocery_exp = expenses.filter(category=MessExpense.Category.GROCERY).aggregate(t=Sum('amount'))['t'] or 0
    utility_exp = expenses.filter(category=MessExpense.Category.UTILITY).aggregate(t=Sum('amount'))['t'] or 0
    other_exp = expenses.filter(category=MessExpense.Category.OTHER).aggregate(t=Sum('amount'))['t'] or 0

    net_balance = total_income - total_expense

    context = {
        'month_filter': month_filter,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'food_exp': food_exp,
        'grocery_exp': grocery_exp,
        'utility_exp': utility_exp,
        'other_exp': other_exp,
        'payments': payments[:30],
        'expenses': expenses,
    }
    return render(request, 'mess/expense_report.html', context)


# ==========================================
# ANNOUNCEMENTS
# ==========================================

@login_required
def announcement_list_view(request):
    """Notice board and announcements list."""
    announcements = Announcement.objects.all().order_by('-published_date')
    is_admin = is_mess_admin(request.user)

    if request.method == 'POST' and is_admin:
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.posted_by = request.user
            ann.save()
            messages.success(request, "Announcement posted successfully!")
            return redirect('announcement_list')
    else:
        form = AnnouncementForm(initial={'published_date': timezone.now().date()})

    context = {
        'announcements': announcements,
        'form': form,
        'is_admin': is_admin,
    }
    return render(request, 'mess/announcements.html', context)


@login_required
def announcement_delete_view(request, pk):
    """Delete an announcement."""
    if not is_mess_admin(request.user):
        return redirect('announcement_list')

    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.delete()
    messages.success(request, "Announcement deleted.")
    return redirect('announcement_list')


# ==========================================
# REPORT EXPORTS (CSV)
# ==========================================

@login_required
def export_students_csv(request):
    """Export all students to CSV."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mess_students_{timezone.now().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'Full Name', 'Department', 'Semester', 'Room No',
        'Phone', 'Email', 'Joining Date', 'Status', 'Monthly Fee', 'Emergency Contact'
    ])
    for s in StudentProfile.objects.all().order_by('student_id'):
        writer.writerow([
            s.student_id, s.full_name, s.department, s.semester, s.hostel_room_no,
            s.phone_number, s.email, s.joining_date, s.get_mess_status_display(),
            s.monthly_mess_fee, s.emergency_contact
        ])
    return response


@login_required
def export_fee_defaulters_csv(request):
    """Export fee defaulters to CSV."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mess_fee_defaulters_{timezone.now().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'Student Name', 'Room No', 'Phone', 'Billing Month',
        'Total Fee (Rs.)', 'Paid (Rs.)', 'Remaining Balance (Rs.)', 'Due Date', 'Status'
    ])
    defaulters = MessFee.objects.filter(
        status__in=[MessFee.FeeStatus.UNPAID, MessFee.FeeStatus.PARTIAL, MessFee.FeeStatus.OVERDUE]
    ).select_related('student')
    for f in defaulters:
        writer.writerow([
            f.student.student_id, f.student.full_name, f.student.hostel_room_no,
            f.student.phone_number, f.billing_month, f.total_fee, f.amount_paid,
            f.remaining_balance, f.due_date, f.get_status_display()
        ])
    return response


@login_required
def export_expenses_csv(request):
    """Export expenses to CSV."""
    if not is_mess_admin(request.user):
        return redirect('student_mess_portal')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mess_expenses_{timezone.now().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Title', 'Amount (Rs.)', 'Description', 'Recorded By'])
    for e in MessExpense.objects.all().order_by('-expense_date'):
        writer.writerow([
            e.expense_date, e.get_category_display(), e.title, e.amount,
            e.description, e.recorded_by.username if e.recorded_by else ''
        ])
    return response
