from datetime import timedelta
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from hostel.models import (
    User, Hostel, Block, Room, Bed, Allotment,
    FeeVoucher, Complaint, GatePass, MessSchedule,
    RoomChangeRequest, Notification, HostelAnnouncement
)


class Command(BaseCommand):
    help = "Populate the database with complete sample data for Ali Hall (300 Rooms, 600 Beds, Special Student Quota, 580 Allocations, 20 Vacancies)."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Setting up 300 Rooms and 580 Allocations via setup_300_rooms..."))
        call_command('setup_300_rooms')

        with transaction.atomic():
            # 1. Administrator & Chief Warden Accounts
            admin_user, _ = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@iub.edu.pk',
                    'first_name': 'Hostel',
                    'last_name': 'Administrator',
                    'role': User.Role.ADMIN,
                    'phone_number': '+92-62-9250235',
                    'cnic_or_id': 'IUB-ADM-1001',
                    'cnic': '3120210010011',
                    'gender': User.Gender.MALE,
                    'address': 'Directorate of Hostels, Baghdad-ul-Jadeed Campus, IUB',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            admin_user.role = User.Role.ADMIN
            admin_user.set_password('admin123')
            admin_user.save()

            chief_warden_user, _ = User.objects.get_or_create(
                username='chief_warden',
                defaults={
                    'email': 'chiefwarden@iub.edu.pk',
                    'first_name': 'Dr. Tariq',
                    'last_name': 'Mahmood',
                    'role': User.Role.CHIEF_WARDEN,
                    'phone_number': '+92-62-9250239',
                    'cnic_or_id': 'IUB-FAC-1001',
                    'cnic': '3120220020021',
                    'gender': User.Gender.MALE,
                    'address': 'Chief Warden Office, Directorate of Hostels, Baghdad-ul-Jadeed Campus, IUB',
                    'is_staff': True,
                    'is_superuser': False,
                }
            )
            chief_warden_user.role = User.Role.CHIEF_WARDEN
            chief_warden_user.set_password('chief123')
            chief_warden_user.save()

            # 2. Hostels
            ali_hall = Hostel.objects.get(name="Ali Hall (Boys Hostel), IUB")
            block_quaid = Block.objects.get(hostel=ali_hall, block_name__icontains="Quaid")
            block_iqbal = Block.objects.get(hostel=ali_hall, block_name__icontains="Iqbal")

            # 3. Wardens
            warden_ali_hall, _ = User.objects.get_or_create(
                username='warden_ali_hall',
                defaults={
                    'email': 'warden.alihall@iub.edu.pk',
                    'first_name': 'Hafiz Muhammad',
                    'last_name': 'Asif',
                    'role': User.Role.WARDEN,
                    'phone_number': '+92-300-9876543',
                    'cnic_or_id': 'IUB-EMP-2045',
                    'cnic': '3120230030031',
                    'gender': User.Gender.MALE,
                    'address': 'Warden Residence, Ali Hall, Baghdad-ul-Jadeed Campus, IUB Bahawalpur',
                    'warden_designation': 'Senior Resident Warden (Quaid Block - Ground Floor)',
                    'assigned_hostel': ali_hall,
                    'assigned_block': block_quaid,
                    'can_manage_allocations': True,
                    'can_manage_complaints': True,
                    'can_manage_gatepasses': True,
                    'can_manage_room_changes': True,
                    'is_staff': True,
                }
            )
            warden_ali_hall.role = User.Role.WARDEN
            warden_ali_hall.set_password('warden123')
            warden_ali_hall.save()

            warden_iqbal, _ = User.objects.get_or_create(
                username='warden_iqbal',
                defaults={
                    'email': 'warden.iqbal@iub.edu.pk',
                    'first_name': 'Engr. Shahbaz',
                    'last_name': 'Khan',
                    'role': User.Role.WARDEN,
                    'phone_number': '+92-301-8765432',
                    'cnic_or_id': 'IUB-EMP-2088',
                    'cnic': '3120240040041',
                    'gender': User.Gender.MALE,
                    'address': 'Ali Hall Staff Quarter #4, IUB Bahawalpur',
                    'warden_designation': 'Block Warden (Iqbal & Sir Syed Blocks)',
                    'assigned_hostel': ali_hall,
                    'assigned_block': block_iqbal,
                    'can_manage_allocations': True,
                    'can_manage_complaints': True,
                    'can_manage_gatepasses': True,
                    'can_manage_room_changes': True,
                    'is_staff': True,
                }
            )
            warden_iqbal.role = User.Role.WARDEN
            warden_iqbal.set_password('warden123')
            warden_iqbal.save()

            # Retrieve key resident students created by setup_300_rooms
            ali = User.objects.get(username='student_ali')
            ali.cnic = '5440166878999'
            ali.cnic_or_id = '5440166878999'
            ali.registration_no = 'FA22-BCS-001'
            ali.semester = '5th'
            ali.save()

            # Backfill CNICs for all students if empty
            for s in User.objects.filter(role=User.Role.STUDENT):
                if not s.cnic and s.cnic_or_id:
                    s.cnic = s.cnic_or_id
                    s.save(update_fields=['cnic'])
            rizwan = User.objects.get(username='student_rizwan')
            usman = User.objects.get(username='student_usman')
            bilal = User.objects.get(username='student_bilal')

            r1 = Room.objects.get(room_number='1')
            r2 = Room.objects.get(room_number='2')
            r105 = Room.objects.get(room_number='105')

            allotment_ali = ali.active_allotment
            allotment_rizwan = rizwan.active_allotment
            allotment_usman = usman.active_allotment
            allotment_bilal = bilal.active_allotment

            # Sample Room Change Request
            rc1, _ = RoomChangeRequest.objects.get_or_create(
                student=bilal,
                current_room=r2,
                defaults={
                    'current_allotment': allotment_bilal,
                    'current_bed': allotment_bilal.bed,
                    'reason_category': RoomChangeRequest.ReasonCategory.MEDICAL,
                    'preferred_room': r105,
                    'detailed_explanation': 'I have knee ligament injury and climbing to upper floors daily causes severe pain. Requesting ground floor room in Quaid Block.',
                    'warden_recommendation': RoomChangeRequest.WardenRecommendation.RECOMMENDED,
                    'warden_remarks': 'Verified medical prescription from Bahawal Victoria Hospital (BVH). Strongly recommended for ground floor transfer.',
                    'reviewed_by_warden': warden_ali_hall,
                    'status': RoomChangeRequest.Status.WARDEN_RECOMMENDED,
                }
            )

            # Sample Complaints
            Complaint.objects.get_or_create(
                student=ali,
                title="Ceiling Fan Speed Regulator Issue in Room 1",
                defaults={
                    'category': Complaint.Category.ELECTRICAL,
                    'priority': Complaint.Priority.HIGH,
                    'room_number': '1',
                    'description': 'The fan speed regulator knob in Quaid Block Room 1 sparks and is stuck on maximum speed.',
                    'status': Complaint.Status.IN_PROGRESS,
                    'assigned_to': warden_ali_hall,
                    'warden_remarks': 'University Electrician assigned by Warden Ali Hall. Work scheduled today.',
                }
            )

            Complaint.objects.get_or_create(
                student=rizwan,
                title="Ground Floor Special Wing Water Cooler Filter Replacement",
                defaults={
                    'category': Complaint.Category.WATER,
                    'priority': Complaint.Priority.URGENT,
                    'room_number': 'Ground Floor Corridor',
                    'description': 'Main electric water cooler filter needs replacement for special scholars wing.',
                    'status': Complaint.Status.RESOLVED,
                    'assigned_to': warden_ali_hall,
                    'warden_remarks': 'Electric water cooler filter changed and sanitized.',
                    'resolved_by': warden_ali_hall,
                    'resolved_at': timezone.now() - timedelta(days=1),
                }
            )

            Complaint.objects.get_or_create(
                student=usman,
                title="WiFi Router Disconnects in Iqbal Block Corridor",
                defaults={
                    'category': Complaint.Category.INTERNET,
                    'priority': Complaint.Priority.MEDIUM,
                    'room_number': '101 Corridor',
                    'description': 'Signal drops frequently between 8 PM to 11 PM on 1st Floor, Iqbal Block.',
                    'status': Complaint.Status.SUBMITTED,
                    'assigned_to': warden_iqbal,
                }
            )

            # Announcements
            HostelAnnouncement.objects.get_or_create(
                title="Ground Floor Special Student Wing Allocation Notice",
                defaults={
                    'category': HostelAnnouncement.Category.GENERAL,
                    'priority': HostelAnnouncement.Priority.IMPORTANT,
                    'content': 'Rooms 1 to 100 on the Ground Floor of Ali Hall are strictly reserved for Special Students (special needs, disabled scholars, and medical considerations) with step-free wheelchair access and dedicated facilities.',
                    'published_by': admin_user,
                    'is_active': True,
                }
            )

            HostelAnnouncement.objects.get_or_create(
                title="Bi-annual Water Filtration & Overhead Tank Disinfection",
                defaults={
                    'category': HostelAnnouncement.Category.MAINTENANCE,
                    'priority': HostelAnnouncement.Priority.URGENT,
                    'content': 'All residents of Ali Hall (Quaid, Iqbal, and Sir Syed blocks) are informed that overhead tanks will be disinfected on Sunday between 8:00 AM to 2:00 PM.',
                    'published_by': admin_user,
                    'is_active': True,
                }
            )

            # Notifications
            Notification.send(
                recipient=ali,
                title="Hostel Room Allocated - Special Quota Ground Floor",
                message="You have been allocated Room 1 (Bed-A) on the Ground Floor Special Wing. Please report to the warden office.",
                notification_type=Notification.Type.ALLOCATION,
                link_url='/profile/'
            )

            Notification.send(
                recipient=rizwan,
                title="Roommate Allocation Confirmed",
                message="You have been allocated Room 1 (Bed-B) alongside Ali Hassan.",
                notification_type=Notification.Type.ALLOCATION,
                link_url='/profile/'
            )

            # Sample Fee Vouchers for Student Ali (Diverse statuses for demo & search)
            FeeVoucher.objects.get_or_create(
                student=ali,
                billing_month="October 2026",
                fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
                defaults={
                    'amount': 5000.00,
                    'issue_date': timezone.now().date() - timedelta(days=25),
                    'due_date': timezone.now().date() - timedelta(days=5),
                    'status': FeeVoucher.Status.PAID,
                    'transaction_id': 'HBL-BWP-77881122',
                    'payment_method': 'HBL Konnect App (IUB Account)',
                    'payment_date': timezone.now().date() - timedelta(days=7),
                    'verified_by': warden_ali_hall,
                    'verified_at': timezone.now() - timedelta(days=6),
                    'remarks': 'Verified against university bank scroll.',
                }
            )

            FeeVoucher.objects.get_or_create(
                student=ali,
                billing_month="November 2026",
                fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
                defaults={
                    'amount': 5000.00,
                    'issue_date': timezone.now().date() - timedelta(days=10),
                    'due_date': timezone.now().date() + timedelta(days=10),
                    'status': FeeVoucher.Status.PENDING_VERIFICATION,
                    'transaction_id': 'HBL-PK-99882244',
                    'payment_method': 'HBL Mobile Banking Transfer',
                    'payment_date': timezone.now().date() - timedelta(days=1),
                    'remarks': 'Voucher proof uploaded by student. Pending admin verification.',
                }
            )

            FeeVoucher.objects.get_or_create(
                student=ali,
                billing_month="December 2026",
                fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
                defaults={
                    'amount': 5000.00,
                    'issue_date': timezone.now().date() - timedelta(days=40),
                    'due_date': timezone.now().date() - timedelta(days=20),
                    'status': FeeVoucher.Status.REJECTED,
                    'transaction_id': 'TRX-INVALID-99',
                    'payment_method': 'Cash Deposit Slip',
                    'payment_date': timezone.now().date() - timedelta(days=22),
                    'verified_by': admin_user,
                    'verified_at': timezone.now() - timedelta(days=19),
                    'remarks': 'Uploaded receipt slip was blurred and transaction ref is not visible. Please re-upload legible proof.',
                }
            )

            FeeVoucher.objects.get_or_create(
                student=ali,
                billing_month="January 2027",
                fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
                defaults={
                    'amount': 5000.00,
                    'issue_date': timezone.now().date(),
                    'due_date': timezone.now().date() + timedelta(days=20),
                    'status': FeeVoucher.Status.UNPAID,
                    'remarks': 'Upcoming semester hostel dues.',
                }
            )

            FeeVoucher.objects.get_or_create(
                student=rizwan,
                billing_month="October 2026",
                fee_type=FeeVoucher.FeeType.HOSTEL_FEE,
                defaults={
                    'amount': 5000.00,
                    'issue_date': timezone.now().date() - timedelta(days=10),
                    'due_date': timezone.now().date() + timedelta(days=15),
                    'status': FeeVoucher.Status.UNPAID,
                    'remarks': 'Regular monthly hostel maintenance fee.',
                }
            )

            # Gate Pass
            GatePass.objects.get_or_create(
                student=ali,
                reason="Weekend family visit to Multan",
                defaults={
                    'destination': 'Multan Cantt',
                    'emergency_contact': '+92-300-1122334',
                    'leave_date': timezone.now() + timedelta(days=2),
                    'return_date': timezone.now() + timedelta(days=4),
                    'status': GatePass.Status.PENDING,
                }
            )

        self.stdout.write(self.style.SUCCESS("Ali Hall Complete Sample Data Populated Successfully!"))
