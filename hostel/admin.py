from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Hostel, Block, Room, Bed, Allotment,
    FeeVoucher, Complaint, GatePass, MessSchedule,
    RoomChangeRequest, Notification, HostelAnnouncement
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'registration_no', 'department', 'application_status', 'is_staff')
    list_filter = ('role', 'application_status', 'is_staff', 'is_superuser', 'gender', 'department')
    fieldsets = UserAdmin.fieldsets + (
        ('Academic & Application Details', {
            'fields': (
                'role', 'registration_no', 'department', 'semester', 'application_status',
                'application_date', 'application_notes', 'reviewed_by', 'reviewed_at',
                'document_cnic', 'document_admission_slip', 'document_other'
            )
        }),
        ('Contact & Emergency', {
            'fields': ('phone_number', 'cnic_or_id', 'gender', 'emergency_contact', 'address', 'profile_pic')
        }),
        ('Warden Assignment & Privileges', {
            'fields': (
                'assigned_hostel', 'assigned_block', 'warden_designation',
                'can_manage_allocations', 'can_manage_complaints',
                'can_manage_gatepasses', 'can_manage_room_changes'
            )
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Hostel Profile', {
            'fields': ('role', 'registration_no', 'department', 'semester', 'phone_number', 'cnic_or_id', 'gender', 'profile_pic')
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'cnic_or_id', 'registration_no')


class BlockInline(admin.TabularInline):
    model = Block
    extra = 1


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender_category', 'total_floors', 'total_rooms_count', 'total_beds_count', 'occupancy_rate')
    list_filter = ('gender_category',)
    search_fields = ('name', 'address')
    inlines = [BlockInline]


class BedInline(admin.TabularInline):
    model = Bed
    extra = 2


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('block_name', 'hostel', 'total_beds_count', 'occupied_beds_count')
    list_filter = ('hostel',)
    search_fields = ('block_name', 'hostel__name')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'block', 'floor', 'room_type', 'capacity', 'price_per_bed', 'maintenance_status', 'available_beds_count')
    list_filter = ('maintenance_status', 'room_type', 'floor', 'block__hostel')
    search_fields = ('room_number', 'block__block_name', 'block__hostel__name')
    inlines = [BedInline]


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_code', 'room', 'get_hostel', 'status', 'current_student')
    list_filter = ('status', 'room__block__hostel')
    search_fields = ('bed_code', 'room__room_number', 'room__block__block_name')

    def get_hostel(self, obj):
        return obj.room.block.hostel.name
    get_hostel.short_description = 'Hostel'


@admin.register(Allotment)
class AllotmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'room', 'bed', 'allotment_date', 'vacate_date', 'is_active')
    list_filter = ('is_active', 'allotment_date', 'room__block__hostel')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'bed__bed_code', 'room__room_number')
    autocomplete_fields = ('student',)


@admin.register(FeeVoucher)
class FeeVoucherAdmin(admin.ModelAdmin):
    list_display = ('voucher_code', 'student', 'fee_type', 'amount', 'due_date', 'status', 'transaction_id')
    list_filter = ('status', 'fee_type', 'due_date')
    search_fields = ('voucher_code', 'student__username', 'transaction_id')
    autocomplete_fields = ('student',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_ref', 'student', 'category', 'priority', 'room_number', 'status', 'assigned_to', 'created_at', 'resolved_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('complaint_ref', 'ticket_number', 'title', 'student__username', 'room_number', 'description')
    autocomplete_fields = ('student', 'assigned_to')


@admin.register(RoomChangeRequest)
class RoomChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('request_code', 'student', 'current_room', 'reason_category', 'status', 'warden_recommendation', 'created_at')
    list_filter = ('status', 'warden_recommendation', 'reason_category', 'created_at')
    search_fields = ('request_code', 'student__username', 'current_room__room_number', 'detailed_explanation')
    autocomplete_fields = ('student',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    autocomplete_fields = ('recipient',)


@admin.register(HostelAnnouncement)
class HostelAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority', 'published_by', 'is_active', 'created_at')
    list_filter = ('category', 'priority', 'is_active')
    search_fields = ('title', 'content')


@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = ('pass_code', 'student', 'destination', 'leave_date', 'return_date', 'status')
    list_filter = ('status', 'leave_date')
    search_fields = ('pass_code', 'student__username', 'destination', 'reason')
    autocomplete_fields = ('student',)


@admin.register(MessSchedule)
class MessScheduleAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'meal_type', 'timing', 'menu_description')
    list_filter = ('day_of_week', 'meal_type')
