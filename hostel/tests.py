from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from hostel.models import (
    User, Hostel, Block, Room, Bed, Allotment, FeeVoucher, Complaint, GatePass,
    RoomChangeRequest, Notification, HostelAnnouncement
)


class SmartHostelModelTests(TestCase):
    def setUp(self):
        # 1. Create users
        self.admin = User.objects.create_user(
            username='admin_test',
            password='password123',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.warden = User.objects.create_user(
            username='warden_test',
            password='password123',
            role=User.Role.WARDEN,
            is_staff=True
        )
        self.student1 = User.objects.create_user(
            username='student1_test',
            password='password123',
            role=User.Role.STUDENT,
            cnic_or_id='ROLL-001',
            department='Computer Science',
            semester=5,
            registration_no='FA22-BCS-001',
            application_status=User.ApplicationStatus.APPROVED
        )
        self.student2 = User.objects.create_user(
            username='student2_test',
            password='password123',
            role=User.Role.STUDENT,
            cnic_or_id='ROLL-002',
            department='Software Engineering',
            semester=3,
            registration_no='FA23-BSE-002',
            application_status=User.ApplicationStatus.APPROVED
        )

        # 2. Create Hostel, Block, Room, Bed
        self.hostel = Hostel.objects.create(
            name="Ali Hall (Boys Hostel), IUB",
            gender_category=Hostel.GenderCategory.BOYS,
            total_floors=3,
            address="Baghdad-ul-Jadeed Campus, IUB"
        )
        self.block = Block.objects.create(hostel=self.hostel, block_name="Quaid Block")
        self.room = Room.objects.create(
            block=self.block,
            room_number="101",
            floor=1,
            room_type=Room.RoomType.DOUBLE,
            capacity=2,
            price_per_bed=5000.00
        )
        self.bed1 = Bed.objects.create(room=self.room, bed_code="Bed-A")
        self.bed2 = Bed.objects.create(room=self.room, bed_code="Bed-B")

    def test_zero_double_booking_logic(self):
        """Test that an occupied bed cannot be double-booked to another student."""
        allotment1 = Allotment.objects.create(
            student=self.student1,
            room=self.room,
            bed=self.bed1,
            is_active=True
        )
        self.bed1.refresh_from_db()
        self.assertEqual(self.bed1.status, Bed.Status.OCCUPIED)
        self.assertEqual(self.student1.active_allotment, allotment1)

        # Try to allot the SAME bed1 to student2 while allotment1 is active -> must fail ValidationError
        with self.assertRaises(ValidationError):
            duplicate_allotment = Allotment(
                student=self.student2,
                room=self.room,
                bed=self.bed1,
                is_active=True
            )
            duplicate_allotment.full_clean()

    def test_student_cannot_have_multiple_active_allotments(self):
        """Test that a single student cannot hold two active beds simultaneously."""
        Allotment.objects.create(
            student=self.student1,
            room=self.room,
            bed=self.bed1,
            is_active=True
        )

        with self.assertRaises(ValidationError):
            second_allotment = Allotment(
                student=self.student1,
                room=self.room,
                bed=self.bed2,
                is_active=True
            )
            second_allotment.full_clean()

    def test_bed_release_on_vacate(self):
        """Test that vacating an allotment releases the bed back to AVAILABLE."""
        allotment = Allotment.objects.create(
            student=self.student1,
            room=self.room,
            bed=self.bed1,
            is_active=True
        )
        self.bed1.refresh_from_db()
        self.assertEqual(self.bed1.status, Bed.Status.OCCUPIED)

        allotment.vacate(remarks="Semester end")
        self.assertFalse(allotment.is_active)
        self.assertIsNotNone(allotment.vacate_date)

        self.bed1.refresh_from_db()
        self.assertEqual(self.bed1.status, Bed.Status.AVAILABLE)

    def test_room_occupancy_status_calculation(self):
        """Test room occupancy status: AVAILABLE -> PARTIALLY_OCCUPIED -> FULLY_OCCUPIED."""
        self.assertEqual(self.room.occupancy_status, 'AVAILABLE')

        Allotment.objects.create(student=self.student1, room=self.room, bed=self.bed1, is_active=True)
        self.assertEqual(self.room.occupancy_status, 'PARTIALLY_OCCUPIED')

        Allotment.objects.create(student=self.student2, room=self.room, bed=self.bed2, is_active=True)
        self.assertEqual(self.room.occupancy_status, 'FULLY_OCCUPIED')

    def test_feevoucher_creation_and_overdue_check(self):
        """Test fee voucher code generation and automatic overdue detection."""
        voucher = FeeVoucher.objects.create(
            student=self.student1,
            fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
            amount=5000.00,
            due_date=timezone.now().date() - timedelta(days=2),
            status=FeeVoucher.Status.UNPAID
        )
        self.assertTrue(voucher.voucher_code.startswith("VCH-"))
        self.assertEqual(voucher.status, FeeVoucher.Status.OVERDUE)
        self.assertTrue(voucher.is_defaulter)

    def test_complaint_ticket_generation_and_categories(self):
        """Test ticket number generation on complaint creation across categories."""
        complaint = Complaint.objects.create(
            student=self.student1,
            category=Complaint.Category.WATER,
            priority=Complaint.Priority.URGENT,
            room_number="101",
            title="Water leakage in washroom",
            description="Tap valve leaking constantly."
        )
        self.assertTrue(complaint.complaint_ref.startswith("CMP-"))
        self.assertEqual(complaint.status, Complaint.Status.SUBMITTED)
        self.assertEqual(complaint.priority, Complaint.Priority.URGENT)

    def test_notification_dispatch(self):
        """Test in-app notification creation and unread count."""
        notif = Notification.send(
            recipient=self.student1,
            title="Room Assigned",
            message="You have been allocated Room 101 Bed-A.",
            notification_type=Notification.Type.ALLOCATION,
            link_url='/profile/'
        )
        self.assertFalse(notif.is_read)
        self.assertEqual(self.student1.unread_notifications_count, 1)


class SmartHostelWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_lead',
            password='password123',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.warden = User.objects.create_user(
            username='warden_lead',
            password='password123',
            role=User.Role.WARDEN,
            is_staff=True,
            can_manage_room_changes=True
        )
        self.student = User.objects.create_user(
            username='student_app',
            password='password123',
            role=User.Role.STUDENT,
            application_status=User.ApplicationStatus.PENDING,
            department='Computer Science',
            registration_no='FA22-BCS-099'
        )

        self.hostel = Hostel.objects.create(name="Ali Hall", gender_category=Hostel.GenderCategory.BOYS, total_floors=3)
        self.block1 = Block.objects.create(hostel=self.hostel, block_name="Quaid Block")
        self.block2 = Block.objects.create(hostel=self.hostel, block_name="Iqbal Block")

        self.room1 = Room.objects.create(block=self.block1, room_number="101", floor=1, capacity=2, price_per_bed=5000.00)
        self.bed1_a = Bed.objects.create(room=self.room1, bed_code="Bed-A")
        self.bed1_b = Bed.objects.create(room=self.room1, bed_code="Bed-B")

        self.room2 = Room.objects.create(block=self.block2, room_number="205", floor=2, capacity=2, price_per_bed=5000.00)
        self.bed2_a = Bed.objects.create(room=self.room2, bed_code="Bed-A")
        self.bed2_b = Bed.objects.create(room=self.room2, bed_code="Bed-B")

    def test_student_application_review_workflow(self):
        """Test admin/warden reviewing student admission application."""
        self.client.login(username='admin_lead', password='password123')
        
        # Approve application
        response = self.client.post(reverse('application_detail', args=[self.student.pk]), {
            'action': 'APPROVE',
            'application_notes': 'Merit verified. Approved for Fall.'
        })
        self.assertEqual(response.status_code, 302)
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.application_status, User.ApplicationStatus.APPROVED)
        self.assertEqual(self.student.reviewed_by, self.admin)
        self.assertIn("Merit verified", self.student.application_notes)

        # Check notification sent to student
        self.assertTrue(Notification.objects.filter(recipient=self.student, notification_type=Notification.Type.APPLICATION).exists())

    def test_atomic_room_change_transfer_workflow(self):
        """Test multi-tier Room Change workflow: Submit -> Warden Review -> Admin Atomic Swap."""
        # Step 1: Allot student into Room 101 Bed-A
        allotment = Allotment.objects.create(
            student=self.student,
            room=self.room1,
            bed=self.bed1_a,
            is_active=True
        )
        self.bed1_a.refresh_from_db()
        self.assertEqual(self.bed1_a.status, Bed.Status.OCCUPIED)

        # Step 2: Student submits room change request
        self.client.login(username='student_app', password='password123')
        post_data = {
            'reason_category': RoomChangeRequest.ReasonCategory.NOISE,
            'preferred_room': self.room2.pk,
            'detailed_explanation': 'Need quieter study environment on 2nd floor.',
        }
        resp = self.client.post(reverse('room_change_request_create'), post_data)
        self.assertEqual(resp.status_code, 302)

        change_req = RoomChangeRequest.objects.get(student=self.student)
        self.assertEqual(change_req.status, RoomChangeRequest.Status.SUBMITTED)
        self.assertEqual(change_req.current_room, self.room1)
        self.assertEqual(change_req.current_bed, self.bed1_a)

        # Step 3: Warden recommends request
        self.client.login(username='warden_lead', password='password123')
        resp_warden = self.client.post(reverse('room_change_detail', args=[change_req.pk]), {
            'action_type': 'WARDEN_RECOMMEND',
            'warden_recommendation': RoomChangeRequest.WardenRecommendation.RECOMMENDED,
            'warden_remarks': 'Verified genuine noise issues near staircase. Recommended.'
        })
        self.assertEqual(resp_warden.status_code, 302)
        change_req.refresh_from_db()
        self.assertEqual(change_req.status, RoomChangeRequest.Status.WARDEN_RECOMMENDED)

        # Step 4: Admin approves and executes ATOMIC BED SWAP
        self.client.login(username='admin_lead', password='password123')
        resp_admin = self.client.post(reverse('room_change_detail', args=[change_req.pk]), {
            'action_type': 'ADMIN_EXECUTE',
            'status': RoomChangeRequest.Status.APPROVED,
            'new_room': self.room2.pk,
            'new_bed': self.bed2_a.pk,
            'admin_remarks': 'Approved by Chief Warden. Transferred to Room 205.'
        })
        self.assertEqual(resp_admin.status_code, 302)

        # Verify atomic transfer effects:
        change_req.refresh_from_db()
        self.assertEqual(change_req.status, RoomChangeRequest.Status.COMPLETED)
        self.assertEqual(change_req.new_room, self.room2)
        self.assertEqual(change_req.new_bed, self.bed2_a)

        # Old bed released to AVAILABLE
        self.bed1_a.refresh_from_db()
        self.assertEqual(self.bed1_a.status, Bed.Status.AVAILABLE)

        # New bed occupied
        self.bed2_a.refresh_from_db()
        self.assertEqual(self.bed2_a.status, Bed.Status.OCCUPIED)

        # Student's active allotment updated to new room and bed
        allotment.refresh_from_db()
        self.assertEqual(allotment.room, self.room2)
        self.assertEqual(allotment.bed, self.bed2_a)
        self.assertTrue(allotment.is_active)


class SmartHostelViewAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_user',
            password='password123',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.warden = User.objects.create_user(
            username='warden_user',
            password='password123',
            role=User.Role.WARDEN,
            is_staff=True
        )
        self.student = User.objects.create_user(
            username='student_user',
            password='password123',
            role=User.Role.STUDENT
        )

    def test_unauthenticated_redirect_to_login(self):
        """Unauthenticated access to dashboard should redirect to login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_student_dashboard_routing(self):
        """Logged in student gets routed to student dashboard."""
        self.client.login(username='student_user', password='password123')
        response = self.client.get(reverse('dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resident Dashboard")

    def test_admin_dashboard_routing(self):
        """Logged in admin gets routed to admin dashboard."""
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator Operations Hub")

    def test_warden_dashboard_routing(self):
        """Logged in warden gets routed to warden operational dashboard."""
        self.client.login(username='warden_user', password='password123')
        response = self.client.get(reverse('dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Warden Operations Dashboard")

    def test_student_blocked_from_staff_only_views(self):
        """Student cannot access admin-only or warden-only endpoints."""
        self.client.login(username='student_user', password='password123')

        # Cannot access warden management
        resp = self.client.get(reverse('warden_list'))
        self.assertEqual(resp.status_code, 302)

        # Cannot access student applications list
        resp = self.client.get(reverse('application_list'))
        self.assertEqual(resp.status_code, 302)

        # Cannot access bed allocation form
        resp = self.client.get(reverse('allocation_create'))
        self.assertEqual(resp.status_code, 302)

        # Cannot access room inventory with all students data
        resp = self.client.get(reverse('room_inventory'))
        self.assertEqual(resp.status_code, 302)

    def test_room_inventory_access_and_filters(self):
        """Admin and warden can access room inventory and filter rooms."""
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('room_inventory'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room-Wise Directory")

    def test_special_students_quota_logic(self):
        """Verify ground floor rooms 1 to 100 are marked as special students quota."""
        hostel = Hostel.objects.create(name="Ali Hall", gender_category=Hostel.GenderCategory.BOYS)
        block = Block.objects.create(hostel=hostel, block_name="Quaid Block")
        special_room = Room.objects.create(
            block=block, room_number="50", floor=1, is_special_quota=True, capacity=2
        )
        regular_room = Room.objects.create(
            block=block, room_number="150", floor=2, is_special_quota=False, capacity=2
        )

        self.assertTrue(special_room.is_special_reserved)
        self.assertIn("Special Students", special_room.quota_category_display)

        self.assertFalse(regular_room.is_special_reserved)
        self.assertIn("Regular Students", regular_room.quota_category_display)

    def test_export_room_inventory_csv(self):
        """Admin can export complete room-wise roster as CSV."""
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('export_room_inventory_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="ali_hall_rooms_roster_', response['Content-Disposition'])


class SmartHostelCNICSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_search',
            password='password123',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.warden = User.objects.create_user(
            username='warden_search',
            password='password123',
            role=User.Role.WARDEN,
            is_staff=True
        )
        self.student = User.objects.create_user(
            username='student_ali_test',
            first_name='Ali',
            last_name='Hassan',
            password='password123',
            role=User.Role.STUDENT,
            cnic='5440166878999',
            cnic_or_id='5440166878999',
            registration_no='FA22-BCS-001',
            department='Computer Science',
            semester='5th',
            phone_number='+92-301-2345678',
            emergency_contact='+92-300-1122334 (Father: M. Hassan)',
            address='Street 4, Muslim Town, Multan'
        )
        self.hostel = Hostel.objects.create(name="Ali Hall", gender_category=Hostel.GenderCategory.BOYS)
        self.block = Block.objects.create(hostel=self.hostel, block_name="Quaid Block")
        self.room = Room.objects.create(block=self.block, room_number="1", floor=1, capacity=2)
        self.bed = Bed.objects.create(room=self.room, bed_code="Bed-A")
        self.allotment = Allotment.objects.create(
            student=self.student,
            room=self.room,
            bed=self.bed,
            is_active=True
        )
        self.voucher = FeeVoucher.objects.create(
            student=self.student,
            billing_month="October 2026",
            fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
            amount=5000.00,
            status=FeeVoucher.Status.PAID,
            transaction_id='HBL-BWP-77881122',
            payment_method='HBL Konnect App',
            due_date=timezone.now().date() + timedelta(days=10)
        )

    def test_admin_search_student_by_raw_cnic(self):
        """Admin searches student by 13-digit CNIC e.g. 5440166878999 and sees all student details."""
        self.client.login(username='admin_search', password='password123')
        url = reverse('student_cnic_search')
        response = self.client.get(url, {'cnic': '5440166878999'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ali Hassan")
        self.assertContains(response, "FA22-BCS-001")
        self.assertContains(response, "5440166878999")
        self.assertContains(response, "Computer Science")
        self.assertContains(response, "5th")
        self.assertContains(response, "Room 1")
        self.assertContains(response, "HBL-BWP-77881122")
        self.assertContains(response, "October 2026")

    def test_admin_search_student_by_hyphenated_cnic(self):
        """Admin searches student using formatted hyphenated CNIC e.g. 54401-6687899-9."""
        self.client.login(username='admin_search', password='password123')
        url = reverse('student_cnic_search')
        response = self.client.get(url, {'cnic': '54401-6687899-9'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ali Hassan")
        self.assertContains(response, "FA22-BCS-001")

    def test_chief_warden_search_student_by_cnic(self):
        """Chief Warden enters a student's CNIC number and retrieves the complete record dossier."""
        chief_warden = User.objects.create_user(
            username='chief_warden_searcher',
            password='password123',
            role=User.Role.CHIEF_WARDEN,
            is_staff=True
        )
        self.client.login(username='chief_warden_searcher', password='password123')
        url = reverse('student_cnic_search')
        response = self.client.get(url, {'cnic': '5440166878999'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ali Hassan")
        self.assertContains(response, "FA22-BCS-001")
        self.assertContains(response, "5440166878999")
        self.assertContains(response, "Computer Science")
        self.assertContains(response, "5th")
        self.assertContains(response, "Room 1")
        self.assertContains(response, "Ali Hall")
        self.assertContains(response, "Total Hostel Fees")
        self.assertContains(response, "Paid Amount")
        self.assertContains(response, "Outstanding Balance")

    def test_search_non_existent_cnic(self):
        """Search displays a friendly warning if no student record matches."""
        self.client.login(username='admin_search', password='password123')
        url = reverse('student_cnic_search')
        response = self.client.get(url, {'cnic': '9999999999999'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No student record found")

    def test_student_cannot_access_cnic_search(self):
        """Students cannot access CNIC search system."""
        self.client.login(username='student_ali_test', password='password123')
        url = reverse('student_cnic_search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class SmartHostelRoleAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='ali_student',
            password='Password123!',
            role=User.Role.STUDENT,
            registration_no='FA22-BCS-001',
            cnic='5440166878999',
            cnic_or_id='5440166878999'
        )
        self.chief_warden = User.objects.create_user(
            username='chief_tariq',
            password='ChiefPassword123!',
            role=User.Role.CHIEF_WARDEN,
            is_staff=True
        )
        self.warden = User.objects.create_user(
            username='warden_asif',
            password='WardenPassword123!',
            role=User.Role.WARDEN,
            is_staff=True
        )

    def test_one_common_login_page_renders_cleanly(self):
        """Single professional login page contains only Roll/User ID, Password, Login button, Forgot Password."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Roll Number or Assigned User ID")
        self.assertContains(response, "Password")
        self.assertContains(response, "Forgot Password?")
        self.assertContains(response, "Sign In")
        # Ensure no student CNIC or role selection cards are displayed
        self.assertNotContains(response, "5440166878999")
        self.assertNotContains(response, "1-Click Role Login")

    def test_automatic_portal_redirection_on_login(self):
        """Users are automatically redirected to their dedicated portal based on authenticated role."""
        # Student -> Student Portal
        resp = self.client.post(reverse('login'), {'username': 'FA22-BCS-001', 'password': 'Password123!'})
        self.assertRedirects(resp, reverse('student_portal'))
        self.client.logout()

        # Warden -> Warden Portal
        resp = self.client.post(reverse('login'), {'username': 'warden_asif', 'password': 'WardenPassword123!'})
        self.assertRedirects(resp, reverse('warden_portal'))
        self.client.logout()

        # Chief Warden -> Chief Warden Portal
        resp = self.client.post(reverse('login'), {'username': 'chief_tariq', 'password': 'ChiefPassword123!'})
        self.assertRedirects(resp, reverse('chief_warden_portal'))
        self.client.logout()

    def test_student_cannot_bypass_to_admin_portal_via_next_param(self):
        """Security: Student logging in with ?next=/portal/admin/ is safely routed to Student Portal."""
        url = reverse('login') + '?next=/portal/admin/'
        resp = self.client.post(url, {'username': 'FA22-BCS-001', 'password': 'Password123!'})
        self.assertRedirects(resp, reverse('student_portal'))

    def test_student_login_by_roll_number(self):
        """Student logs in with university roll number and password."""
        logged_in = self.client.login(username='FA22-BCS-001', password='Password123!')
        self.assertTrue(logged_in)
        response = self.client.get(reverse('student_portal'))
        self.assertEqual(response.status_code, 200)

    def test_student_login_by_cnic(self):
        """Student logs in with CNIC and password."""
        logged_in = self.client.login(username='5440166878999', password='Password123!')
        self.assertTrue(logged_in)
        response = self.client.get(reverse('student_portal'))
        self.assertEqual(response.status_code, 200)

    def test_chief_warden_login_and_portal(self):
        """Chief Warden logs in and accesses dedicated Chief Warden Portal."""
        logged_in = self.client.login(username='chief_tariq', password='ChiefPassword123!')
        self.assertTrue(logged_in)
        response = self.client.get(reverse('chief_warden_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chief Warden")

    def test_warden_login_and_portal(self):
        """Warden logs in and accesses dedicated Warden Block Portal."""
        logged_in = self.client.login(username='warden_asif', password='WardenPassword123!')
        self.assertTrue(logged_in)
        response = self.client.get(reverse('warden_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Warden")


class SmartHostelPortalPrivacyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student_res',
            password='password123',
            role=User.Role.STUDENT,
            cnic='5440166878999'
        )
        self.other_student = User.objects.create_user(
            username='other_student',
            password='password123',
            role=User.Role.STUDENT,
            cnic='3120299887766'
        )
        self.other_voucher = FeeVoucher.objects.create(
            student=self.other_student,
            billing_month="October 2026",
            fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
            amount=5000.00,
            status=FeeVoucher.Status.UNPAID,
            due_date=timezone.now().date() + timedelta(days=10)
        )

    def test_student_blocked_from_admin_portal(self):
        self.client.login(username='student_res', password='password123')
        response = self.client.get(reverse('admin_portal'))
        self.assertEqual(response.status_code, 302)

    def test_student_blocked_from_chief_warden_portal(self):
        self.client.login(username='student_res', password='password123')
        response = self.client.get(reverse('chief_warden_portal'))
        self.assertEqual(response.status_code, 302)

    def test_student_blocked_from_warden_portal(self):
        self.client.login(username='student_res', password='password123')
        response = self.client.get(reverse('warden_portal'))
        self.assertEqual(response.status_code, 302)

    def test_student_blocked_from_room_inventory_all_students(self):
        self.client.login(username='student_res', password='password123')
        response = self.client.get(reverse('room_inventory'))
        self.assertEqual(response.status_code, 302)

    def test_student_cannot_view_other_student_voucher(self):
        self.client.login(username='student_res', password='password123')
        response = self.client.get(reverse('fee_voucher_detail', kwargs={'pk': self.other_voucher.pk}))
        self.assertIn(response.status_code, [302, 404])


class SmartHostelFeeUploadAndVerifyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_verify',
            password='password123',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.student = User.objects.create_user(
            username='student_fee_user',
            password='password123',
            role=User.Role.STUDENT,
            registration_no='FA22-BCS-099',
            cnic='5440166878999'
        )
        self.voucher = FeeVoucher.objects.create(
            student=self.student,
            billing_month="October 2026",
            fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
            amount=5000.00,
            status=FeeVoucher.Status.UNPAID,
            due_date=timezone.now().date() + timedelta(days=10)
        )

    def test_student_uploads_fee_voucher_valid_file(self):
        """Student successfully uploads fee voucher with JPG receipt."""
        self.client.login(username='student_fee_user', password='password123')
        receipt = SimpleUploadedFile("receipt.jpg", b"\xff\xd8\xff dummy jpeg content", content_type="image/jpeg")
        post_data = {
            'fee_type': FeeVoucher.FeeType.HOSTEL_FEE,
            'billing_month': 'October 2026',
            'amount': '5000.00',
            'payment_method': 'HBL Mobile Banking Transfer',
            'transaction_id': 'TXN-99887711',
            'payment_date': timezone.now().date().isoformat(),
            'payment_proof': receipt,
            'remarks': 'Paid via mobile banking app'
        }
        response = self.client.post(reverse('student_fee_upload'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        voucher = FeeVoucher.objects.filter(student=self.student, transaction_id='TXN-99887711').first()
        self.assertIsNotNone(voucher)
        self.assertEqual(voucher.status, FeeVoucher.Status.PENDING_VERIFICATION)
        self.assertTrue(voucher.payment_proof.name)

    def test_student_uploads_fee_voucher_invalid_file(self):
        """Student uploading invalid file format (.exe) is rejected with error."""
        self.client.login(username='student_fee_user', password='password123')
        bad_file = SimpleUploadedFile("script.exe", b"MZ executable content", content_type="application/octet-stream")
        post_data = {
            'fee_type': FeeVoucher.FeeType.HOSTEL_FEE,
            'billing_month': 'October 2026',
            'amount': '5000.00',
            'payment_method': 'Cash',
            'transaction_id': 'TXN-BAD-FILE',
            'payment_date': timezone.now().date().isoformat(),
            'payment_proof': bad_file,
        }
        response = self.client.post(reverse('student_fee_upload'), post_data)
        self.assertContains(response, "Invalid file format")

    def test_admin_approves_fee_voucher(self):
        """Admin verifies payment and updates status to PAID."""
        self.voucher.status = FeeVoucher.Status.PENDING_VERIFICATION
        self.voucher.transaction_id = 'TXN-PENDING-01'
        self.voucher.save()

        self.client.login(username='admin_verify', password='password123')
        url = reverse('fee_verify', kwargs={'pk': self.voucher.pk})
        post_data = {
            'status': FeeVoucher.Status.PAID,
            'remarks': 'Verified against bank transaction feed. Amount received.'
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.status, FeeVoucher.Status.PAID)
        self.assertEqual(self.voucher.verified_by, self.admin)
        notif = Notification.objects.filter(recipient=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn("Fee Payment Paid", notif.title)

    def test_admin_rejects_fee_voucher_with_remarks(self):
        """Admin rejects fee voucher with explanation remarks."""
        self.voucher.status = FeeVoucher.Status.PENDING_VERIFICATION
        self.voucher.save()

        self.client.login(username='admin_verify', password='password123')
        url = reverse('fee_verify', kwargs={'pk': self.voucher.pk})
        post_data = {
            'status': FeeVoucher.Status.REJECTED,
            'remarks': 'Uploaded voucher slip is unreadable. Please upload a clear photo.'
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.status, FeeVoucher.Status.REJECTED)
        self.assertIn("unreadable", self.voucher.remarks)


class SmartHostelRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.existing_student = User.objects.create_user(
            username='existing_ali',
            email='existing_ali@student.iub.edu.pk',
            password='Password123!',
            role=User.Role.STUDENT,
            registration_no='FA22-BCS-100',
            cnic='5440111111111',
            cnic_or_id='5440111111111'
        )

    def test_successful_student_registration_and_auto_login(self):
        """Registering with valid data saves account, hashes password, logs in without ValueError, and redirects to student portal."""
        data = {
            'username': 'new_scholar',
            'first_name': 'Ahmad',
            'last_name': 'Raza',
            'email': 'ahmad.raza@student.iub.edu.pk',
            'phone_number': '+92-300-9988776',
            'registration_no': 'FA24-BCS-055',
            'department': 'Computer Science',
            'semester': '1st',
            'cnic_or_id': '5440166878999',
            'gender': User.Gender.MALE,
            'emergency_contact': '+92-301-1122334 (Father)',
            'address': 'House 5, Street 2, Model Town, Bahawalpur',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        }
        response = self.client.post(reverse('register'), data, follow=True)
        # Should succeed without ValueError and follow redirect to Student Portal
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resident Dashboard")
        self.assertContains(response, "Registration successful")

        # Verify DB record
        new_user = User.objects.filter(username='new_scholar').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, User.Role.STUDENT)
        self.assertEqual(new_user.application_status, User.ApplicationStatus.PENDING)
        self.assertTrue(new_user.check_password('SecurePassword123!'))
        self.assertEqual(new_user.registration_no, 'FA24-BCS-055')

    def test_duplicate_registration_no_rejected(self):
        """Attempting to register with an already existing roll number fails validation."""
        data = {
            'username': 'another_student',
            'first_name': 'Kamran',
            'last_name': 'Khan',
            'email': 'kamran@student.iub.edu.pk',
            'phone_number': '+92-300-1111222',
            'registration_no': 'FA22-BCS-100',  # Duplicate!
            'department': 'Computer Science',
            'semester': '1st',
            'cnic_or_id': '5440199999999',
            'gender': User.Gender.MALE,
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_duplicate_cnic_rejected(self):
        """Attempting to register with an already existing CNIC fails validation."""
        data = {
            'username': 'student_same_cnic',
            'first_name': 'Zahid',
            'last_name': 'Iqbal',
            'email': 'zahid@student.iub.edu.pk',
            'phone_number': '+92-300-3333444',
            'registration_no': 'FA24-BIT-012',
            'department': 'Information Technology',
            'semester': '1st',
            'cnic_or_id': '5440111111111',  # Duplicate CNIC!
            'gender': User.Gender.MALE,
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already registered")

    def test_password_mismatch_rejected(self):
        """Mismatched password and confirm_password fails validation."""
        data = {
            'username': 'mismatched_student',
            'first_name': 'Tariq',
            'last_name': 'Aziz',
            'email': 'tariq.aziz@student.iub.edu.pk',
            'phone_number': '+92-300-4444555',
            'registration_no': 'FA24-BSE-088',
            'department': 'Software Engineering',
            'semester': '1st',
            'cnic_or_id': '5440188888888',
            'gender': User.Gender.MALE,
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword999!',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")


