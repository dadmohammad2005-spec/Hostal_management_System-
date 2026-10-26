from django.contrib import admin
from .models import (
    StudentProfile, MealMenu, MealAttendance, MessFee, FeePayment, MessExpense, Announcement
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'department', 'semester', 'hostel_room_no', 'phone_number', 'mess_status', 'is_active')
    list_filter = ('mess_status', 'department', 'semester', 'is_active')
    search_fields = ('student_id', 'full_name', 'phone_number', 'hostel_room_no', 'email')


@admin.register(MealMenu)
class MealMenuAdmin(admin.ModelAdmin):
    list_display = ('date', 'day_of_week', 'meal_type', 'serving_time', 'menu_items', 'status')
    list_filter = ('meal_type', 'day_of_week', 'status', 'date')
    search_fields = ('menu_items', 'special_instructions')


@admin.register(MealAttendance)
class MealAttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'meal_type', 'student', 'status', 'marked_at')
    list_filter = ('meal_type', 'status', 'date')
    search_fields = ('student__student_id', 'student__full_name')


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 1


@admin.register(MessFee)
class MessFeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'billing_month', 'total_fee', 'amount_paid', 'remaining_balance', 'due_date', 'status')
    list_filter = ('status', 'billing_month', 'due_date')
    search_fields = ('student__student_id', 'student__full_name', 'billing_month')
    inlines = [FeePaymentInline]


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'mess_fee', 'amount', 'payment_date', 'payment_method', 'transaction_id')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('student__student_id', 'student__full_name', 'transaction_id')


@admin.register(MessExpense)
class MessExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'expense_date', 'recorded_by')
    list_filter = ('category', 'expense_date')
    search_fields = ('title', 'description')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority', 'published_date', 'is_active')
    list_filter = ('category', 'priority', 'is_active')
    search_fields = ('title', 'content')
