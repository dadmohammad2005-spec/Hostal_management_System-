from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from mess.models import (
    StudentProfile, MealMenu, MealAttendance, MessFee, FeePayment, MessExpense, Announcement
)

User = get_user_model()


class StudentProfileModelTest(TestCase):
    def setUp(self):
        self.student = StudentProfile.objects.create(
            student_id="FA22-BCS-001",
            full_name="Muhammad Ali",
            department="Computer Science",
            semester=StudentProfile.Semester.SEM_5,
            phone_number="03001234567",
            hostel_room_no="Room 101-A",
            email="ali@example.com",
            monthly_mess_fee=Decimal("4500.00"),
            emergency_contact="Father: 03009876543",
        )

    def test_student_str(self):
        self.assertEqual(str(self.student), "FA22-BCS-001 - Muhammad Ali (Room 101-A)")

    def test_initials_property(self):
        self.assertEqual(self.student.initials, "MA")
        self.student.full_name = "Hamza"
        self.assertEqual(self.student.initials, "HA")
        self.student.full_name = ""
        self.assertEqual(self.student.initials, "ST")

    def test_total_outstanding_balance(self):
        # Initial balance should be 0 since no fees created
        self.assertEqual(self.student.total_outstanding_balance, Decimal("0.00"))

        fee1 = MessFee.objects.create(
            student=self.student,
            billing_month="September 2026",
            month_date=date(2026, 9, 1),
            total_fee=Decimal("4500.00"),
            amount_paid=Decimal("2000.00"),
            due_date=date(2026, 9, 10),
            status=MessFee.FeeStatus.PARTIAL
        )
        fee2 = MessFee.objects.create(
            student=self.student,
            billing_month="October 2026",
            month_date=date(2026, 10, 1),
            total_fee=Decimal("4500.00"),
            amount_paid=Decimal("0.00"),
            due_date=date(2026, 10, 10),
            status=MessFee.FeeStatus.UNPAID
        )
        # Outstanding: (4500 - 2000) + (4500 - 0) = 2500 + 4500 = 7000
        self.assertEqual(self.student.total_outstanding_balance, Decimal("7000.00"))


class MealMenuModelTest(TestCase):
    def test_meal_menu_creation_and_auto_day(self):
        test_date = date(2026, 10, 26)  # Monday
        menu = MealMenu.objects.create(
            date=test_date,
            meal_type=MealMenu.MealType.BREAKFAST,
            menu_items="Halwa Puri, Chana, Tea",
            serving_time="7:30 AM - 9:00 AM"
        )
        self.assertEqual(menu.day_of_week, "MONDAY")
        self.assertIn("Breakfast", str(menu))

    def test_unique_daily_meal_menu_constraint(self):
        test_date = date(2026, 10, 26)
        MealMenu.objects.create(
            date=test_date,
            meal_type=MealMenu.MealType.LUNCH,
            menu_items="Chicken Biryani",
            serving_time="1:00 PM - 2:30 PM"
        )
        with self.assertRaises(IntegrityError):
            MealMenu.objects.create(
                date=test_date,
                meal_type=MealMenu.MealType.LUNCH,
                menu_items="Beef Pulao",
                serving_time="1:00 PM - 2:30 PM"
            )


class MealAttendanceModelTest(TestCase):
    def setUp(self):
        self.student = StudentProfile.objects.create(
            student_id="FA22-BCS-002",
            full_name="Bilal Tariq",
            department="Software Engineering",
            phone_number="03011112222",
            hostel_room_no="Room 102-B",
            email="bilal@example.com"
        )

    def test_meal_attendance_creation(self):
        att = MealAttendance.objects.create(
            student=self.student,
            date=date(2026, 10, 23),
            meal_type=MealMenu.MealType.DINNER,
            status=MealAttendance.AttendanceStatus.PRESENT
        )
        self.assertEqual(att.status, MealAttendance.AttendanceStatus.PRESENT)
        self.assertIn("FA22-BCS-002", str(att))

    def test_unique_student_meal_attendance_constraint(self):
        today = date(2026, 10, 23)
        MealAttendance.objects.create(
            student=self.student,
            date=today,
            meal_type=MealMenu.MealType.BREAKFAST,
            status=MealAttendance.AttendanceStatus.PRESENT
        )
        # Attempting to create duplicate attendance for same student, date, and meal type must fail
        with self.assertRaises(IntegrityError):
            MealAttendance.objects.create(
                student=self.student,
                date=today,
                meal_type=MealMenu.MealType.BREAKFAST,
                status=MealAttendance.AttendanceStatus.ABSENT
            )


class MessFeeAndPaymentTest(TestCase):
    def setUp(self):
        self.student = StudentProfile.objects.create(
            student_id="FA22-BCS-003",
            full_name="Usman Ghani",
            department="Computer Science",
            phone_number="03023334444",
            hostel_room_no="Room 103-A",
            email="usman@example.com",
            monthly_mess_fee=Decimal("4500.00")
        )
        self.fee = MessFee.objects.create(
            student=self.student,
            billing_month="October 2026",
            month_date=date(2026, 10, 1),
            total_fee=Decimal("4500.00"),
            due_date=date(2026, 10, 15),
            status=MessFee.FeeStatus.UNPAID
        )

    def test_initial_fee_balance(self):
        self.assertEqual(self.fee.remaining_balance, Decimal("4500.00"))
        self.assertEqual(self.fee.amount_paid, Decimal("0.00"))
        self.assertEqual(self.fee.status, MessFee.FeeStatus.UNPAID)

    def test_partial_payment_updates_fee_record(self):
        payment1 = FeePayment.objects.create(
            mess_fee=self.fee,
            student=self.student,
            amount=Decimal("2000.00"),
            payment_method=FeePayment.PaymentMethod.CASH,
            transaction_id="CASH-001"
        )
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.amount_paid, Decimal("2000.00"))
        self.assertEqual(self.fee.remaining_balance, Decimal("2500.00"))
        self.assertEqual(self.fee.status, MessFee.FeeStatus.PARTIAL)

    def test_full_payment_sets_paid_status(self):
        FeePayment.objects.create(
            mess_fee=self.fee,
            student=self.student,
            amount=Decimal("4500.00"),
            payment_method=FeePayment.PaymentMethod.EASYPAISA,
            transaction_id="EP-789012"
        )
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.amount_paid, Decimal("4500.00"))
        self.assertEqual(self.fee.remaining_balance, Decimal("0.00"))
        self.assertEqual(self.fee.status, MessFee.FeeStatus.PAID)

    def test_unique_student_monthly_mess_fee(self):
        with self.assertRaises(IntegrityError):
            MessFee.objects.create(
                student=self.student,
                billing_month="October 2026",
                month_date=date(2026, 10, 1),
                total_fee=Decimal("4500.00"),
                due_date=date(2026, 10, 15)
            )


class MessExpenseAndAnnouncementTest(TestCase):
    def test_expense_creation(self):
        exp = MessExpense.objects.create(
            category=MessExpense.Category.FOOD,
            title="30kg Fresh Chicken",
            expense_date=date(2026, 10, 23),
            amount=Decimal("19500.00"),
            description="Purchased from Bahawalpur Model Town Poultry"
        )
        self.assertEqual(exp.category, MessExpense.Category.FOOD)
        self.assertIn("19500", str(exp))

    def test_announcement_creation(self):
        ann = Announcement.objects.create(
            title="Special Biryani Dinner this Friday",
            category=Announcement.Category.SPECIAL_MEAL,
            priority=Announcement.Priority.IMPORTANT,
            content="Hostel mess will serve special chicken biryani and kheer."
        )
        self.assertTrue(ann.is_active)
        self.assertIn("Special Biryani", str(ann))


class RoleBasedAccessControlTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin user
        self.admin_user = User.objects.create_superuser(
            username='mess_admin',
            email='admin@iub.edu.pk',
            password='adminpassword123'
        )

        # Student user with linked profile
        self.student_user = User.objects.create_user(
            username='fa22-bcs-099',
            email='student99@iub.edu.pk',
            password='studentpassword123'
        )
        if hasattr(self.student_user, 'role'):
            self.student_user.role = 'STUDENT'
            self.student_user.save()

        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='FA22-BCS-099',
            full_name='Ahmad Raza',
            department='Computer Science',
            phone_number='03055556666',
            hostel_room_no='Room 205-C',
            email='student99@iub.edu.pk',
            monthly_mess_fee=Decimal('4500.00')
        )

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse('mess_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_student_visiting_dashboard_redirected_to_portal(self):
        self.client.login(username='fa22-bcs-099', password='studentpassword123')
        response = self.client.get(reverse('mess_dashboard'))
        # Should render the student portal template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mess/student_portal.html')
        self.assertContains(response, 'Ahmad Raza')

    def test_student_restricted_from_admin_views(self):
        self.client.login(username='fa22-bcs-099', password='studentpassword123')

        admin_urls = [
            reverse('student_list'),
            reverse('student_create'),
            reverse('attendance_mark'),
            reverse('fee_list'),
            reverse('fee_bulk_generate'),
            reverse('expense_list'),
        ]
        for url in admin_urls:
            response = self.client.get(url)
            # Student should be redirected to their portal
            self.assertEqual(response.status_code, 302, f"Failed restricting student on {url}")
            self.assertIn(reverse('student_mess_portal'), response.url)

    def test_admin_can_access_dashboard_and_student_list(self):
        self.client.login(username='mess_admin', password='adminpassword123')
        
        # Test Admin Dashboard
        response = self.client.get(reverse('mess_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mess/admin_dashboard.html')

        # Test Student List
        response = self.client.get(reverse('student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FA22-BCS-099')

    def test_student_profile_self_edit(self):
        self.client.login(username='fa22-bcs-099', password='studentpassword123')
        
        # Get self edit page
        response = self.client.get(reverse('student_self_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mess/student_self_edit.html')

        # Post update for permitted fields
        response = self.client.post(reverse('student_self_edit'), {
            'phone_number': '03099998888',
            'emergency_contact': 'Uncle: 03088887777',
        })
        self.assertRedirects(response, reverse('student_mess_portal'))
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.phone_number, '03099998888')
        self.assertEqual(self.student_profile.emergency_contact, 'Uncle: 03088887777')
        # Room number and student ID must remain unchanged
        self.assertEqual(self.student_profile.hostel_room_no, 'Room 205-C')
        self.assertEqual(self.student_profile.student_id, 'FA22-BCS-099')

    def test_csv_exports_admin_only(self):
        # Student cannot export
        self.client.login(username='fa22-bcs-099', password='studentpassword123')
        response = self.client.get(reverse('export_mess_students_csv'))
        self.assertEqual(response.status_code, 302)

        # Admin can export
        self.client.login(username='mess_admin', password='adminpassword123')
        response = self.client.get(reverse('export_mess_students_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Student ID,Full Name,Department', response.content.decode('utf-8'))
