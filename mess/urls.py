from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Portals
    path('', views.mess_dashboard_router, name='mess_dashboard'),
    path('portal/', views.student_mess_portal, name='student_mess_portal'),
    path('portal/profile/edit/', views.student_profile_self_edit, name='student_self_edit'),

    # Student Management
    path('students/', views.student_list_view, name='student_list'),
    path('students/add/', views.student_create_view, name='student_create'),
    path('students/<int:pk>/', views.student_detail_view, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit_view, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete_view, name='student_delete'),

    # Meal Menu Management
    path('menu/weekly/', views.menu_weekly_view, name='menu_weekly'),
    path('menu/add/', views.menu_create_view, name='menu_create'),
    path('menu/<int:pk>/edit/', views.menu_edit_view, name='menu_edit'),
    path('menu/<int:pk>/delete/', views.menu_delete_view, name='menu_delete'),

    # Meal Attendance
    path('attendance/', views.attendance_mark_view, name='attendance_mark'),
    path('attendance/report/', views.attendance_report_view, name='attendance_report'),

    # Mess Fees
    path('fees/', views.fee_list_view, name='fee_list'),
    path('fees/bulk-generate/', views.fee_bulk_generate_view, name='fee_bulk_generate'),
    path('fees/payment/', views.fee_payment_create_view, name='fee_payment_create'),
    path('fees/payment/<int:fee_id>/', views.fee_payment_create_view, name='fee_payment_for_invoice'),

    # Mess Expenses
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/report/', views.expense_report_view, name='expense_report'),

    # Announcements
    path('announcements/', views.announcement_list_view, name='announcement_list'),
    path('announcements/<int:pk>/delete/', views.announcement_delete_view, name='announcement_delete'),

    # CSV Exports
    path('reports/export/students/', views.export_students_csv, name='export_mess_students_csv'),
    path('reports/export/defaulters/', views.export_fee_defaulters_csv, name='export_mess_defaulters_csv'),
    path('reports/export/expenses/', views.export_expenses_csv, name='export_mess_expenses_csv'),
]
