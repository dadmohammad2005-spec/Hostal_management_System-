from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Portals
    path('', views.dashboard_router, name='dashboard'),
    path('portal/admin/', views.admin_portal_view, name='admin_portal'),
    path('portal/chief-warden/', views.chief_warden_portal_view, name='chief_warden_portal'),
    path('portal/warden/', views.warden_portal_view, name='warden_portal'),
    path('portal/student/', views.student_portal_view, name='student_portal'),
    path('profile/', views.profile_view, name='profile'),

    # Authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # Notifications System
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all/', views.notification_mark_all_read, name='notification_mark_all_read'),

    # Student Applications
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),

    # Student Directory (Dossier)
    path('students/', views.student_directory, name='student_directory'),
    path('students/<int:pk>/', views.student_detail_view, name='student_detail_view'),

    # Allocations & Rooms (300 Rooms, 600 Beds)
    path('allocations/', views.allocation_list, name='allocation_list'),
    path('allocations/new/', views.allocation_create, name='allocation_create'),
    path('allocations/<int:pk>/vacate/', views.allocation_vacate, name='allocation_vacate'),
    path('rooms/', views.room_inventory, name='room_inventory'),
    path('rooms/<int:pk>/maintenance-toggle/', views.room_maintenance_toggle, name='room_maintenance_toggle'),
    path('api/available-beds/', views.get_available_beds_api, name='api_available_beds'),

    # Student Room-Change Requests
    path('room-changes/', views.room_change_list, name='room_change_list'),
    path('room-changes/request/', views.room_change_request_create, name='room_change_request_create'),
    path('room-changes/<int:pk>/', views.room_change_detail, name='room_change_detail'),

    # Maintenance & Complaints (11 Categories)
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/new/', views.complaint_create, name='complaint_create'),
    path('complaints/<int:pk>/', views.complaint_detail, name='complaint_detail'),

    # Warden Management (Admin Only)
    path('wardens/', views.warden_list, name='warden_list'),
    path('wardens/new/', views.warden_create, name='warden_create'),
    path('wardens/<int:pk>/edit/', views.warden_edit, name='warden_edit'),

    # Hostel Announcements / Notice Board
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/new/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),

    # Fee Management
    path('fees/', views.fee_voucher_list, name='fee_voucher_list'),
    path('fees/upload/', views.student_fee_upload, name='fee_voucher_upload'),
    path('portal/student/upload-voucher/', views.student_fee_upload, name='student_fee_upload'),
    path('fees/create/', views.fee_voucher_create, name='fee_voucher_create'),
    path('fees/bulk-generate/', views.bulk_fee_generate, name='bulk_fee_generate'),
    path('fees/<int:pk>/pay/', views.fee_submit_payment, name='fee_submit_payment'),
    path('fees/<int:pk>/verify/', views.fee_verify, name='fee_verify'),
    path('fees/<int:pk>/voucher/', views.fee_voucher_detail, name='fee_voucher_detail'),

    # Student CNIC Search System
    path('cnic-search/', views.student_cnic_search, name='student_cnic_search'),
    path('portal/admin/cnic-search/', views.student_cnic_search, name='admin_cnic_search'),

    # Gate Pass
    path('gatepasses/', views.gate_pass_list, name='gate_pass_list'),
    path('gatepasses/request/', views.gate_pass_request, name='gate_pass_request'),
    path('gatepasses/<int:pk>/<str:action>/', views.gate_pass_action, name='gate_pass_action'),

    # Mess Timetable
    path('mess/', views.mess_menu_view, name='mess_menu'),
    path('mess/edit/', views.mess_menu_edit, name='mess_menu_edit'),

    # Exports
    path('reports/export-rooms/', views.export_room_inventory_csv, name='export_room_inventory_csv'),
    path('reports/export-students/', views.export_students_csv, name='export_students_csv'),
    path('reports/export-defaulters/', views.export_fee_defaulters_csv, name='export_fee_defaulters_csv'),
]
