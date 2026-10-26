from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from hostel.models import User, Hostel, Block, Room, Bed, Allotment


class Command(BaseCommand):
    help = "Configure Ali Hall 300 rooms (Rooms 1-100 Ground Floor Special Quota, Rooms 101-300 Regular) with 580 allocated students leaving 20 spaces vacant."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Setting up Ali Hall 300 Rooms, 600 Beds, Special Student Quota, and 580 Allocations..."))

        first_names = [
            'Ali', 'Rizwan', 'Usman', 'Bilal', 'Hamza', 'Tariq', 'Zain', 'Farooq', 'Ahmed', 'Hassan',
            'Imran', 'Kamran', 'Babar', 'Shaheen', 'Shadab', 'Haris', 'Fakhar', 'Naseem', 'Asif', 'Saqib',
            'Kashif', 'Danish', 'Faisal', 'Junaid', 'Naveed', 'Waqas', 'Zeeshan', 'Mohsin', 'Adnan', 'Umair',
            'Shahid', 'Zahid', 'Arslan', 'Shoaib', 'Sohail', 'Waseem', 'Tanveer', 'Adeel', 'Noman', 'Rehan',
            'Ahsan', 'Atif', 'Irfan', 'Aftab', 'Mubashir', 'Shahbaz', 'Qasim', 'Rashid', 'Waqar', 'Azhar',
            'Mustafa', 'Haider', 'Talha', 'Moazzam', 'Suleman', 'Faizan', 'Subhan', 'Hammad', 'Abdullah', 'Huzaifa',
            'Ubaid', 'Ammar', 'Shayan', 'Zubair', 'Shahrukh', 'Yasir', 'Nouman', 'Shahzad', 'Ghulam', 'Murad'
        ]

        last_names = [
            'Khan', 'Ahmed', 'Hassan', 'Tariq', 'Malik', 'Rehman', 'Iqbal', 'Shah', 'Mehmood', 'Chaudhry',
            'Bhatti', 'Jutt', 'Awan', 'Siddiqui', 'Qureshi', 'Abbasi', 'Gondal', 'Warraich', 'Ansari', 'Mirza',
            'Raza', 'Farooqi', 'Hashmi', 'Gill', 'Cheema', 'Sial', 'Dasti', 'Khosa', 'Mazzari', 'Laghari'
        ]

        departments_list = [
            ('Computer Science', 'BCS'),
            ('Software Engineering', 'BSE'),
            ('Information Technology', 'BIT'),
            ('Electrical Engineering', 'BEE'),
            ('Civil Engineering', 'BCE'),
            ('Mechanical Engineering', 'BME'),
            ('Chemistry', 'CHM'),
            ('Physics', 'PHY'),
            ('Mathematics', 'MTH'),
            ('Management Sciences', 'BBA'),
            ('Pharmacy (Pharm-D)', 'PHD'),
            ('Agriculture', 'AGR'),
            ('Law (LLB)', 'LLB'),
            ('Biochemistry', 'BCH'),
            ('Economics', 'ECO'),
        ]

        cities_addresses = [
            ('House 14, Model Town, Bahawalpur', 'Bahawalpur'),
            ('Street 3, Baghdad-ul-Jadeed Road, Bahawalpur', 'Bahawalpur'),
            ('One Unit Staff Colony, Bahawalpur', 'Bahawalpur'),
            ('House 8, Shadman Town, Bahawalpur', 'Bahawalpur'),
            ('Street 5, Muslim Town, Multan', 'Multan'),
            ('House 22, Cantt Area, Multan', 'Multan'),
            ('Gulgasht Colony, Multan', 'Multan'),
            ('Block 4, Gulshan-e-Iqbal, Rahim Yar Khan', 'Rahim Yar Khan'),
            ('Model Town, Rahim Yar Khan', 'Rahim Yar Khan'),
            ('Abbasia Town, Rahim Yar Khan', 'Rahim Yar Khan'),
            ('Ward 5, Mohallah Sheikhan, Ahmedpur East, Bahawalpur', 'Ahmedpur East'),
            ('Model Town, Ahmedpur East', 'Ahmedpur East'),
            ('Colony Road, Hasilpur, Bahawalpur', 'Hasilpur'),
            ('Circular Road, Mohallah Islam Pura, Lodhran', 'Lodhran'),
            ('Railway Road, Lodhran', 'Lodhran'),
            ('Jampur Road, Dera Ghazi Khan', 'Dera Ghazi Khan'),
            ('Block 12, Khyaban-e-Sarwar, Dera Ghazi Khan', 'Dera Ghazi Khan'),
            ('Farid Town, Sahiwal', 'Sahiwal'),
            ('Gulberg III, Lahore', 'Lahore'),
            ('Madina Town, Faisalabad', 'Faisalabad'),
            ('Al-Rehman Colony, Muzaffargarh', 'Muzaffargarh'),
            ('Railway Road, Khanewal', 'Khanewal'),
            ('Mian Channu, Khanewal', 'Khanewal'),
            ('Shikarpur Road, Bahawalnagar', 'Bahawalnagar'),
            ('Chishtian, Bahawalnagar', 'Bahawalnagar'),
            ('Haroonabad, Bahawalnagar', 'Bahawalnagar'),
            ('Kot Addu, Muzaffargarh', 'Muzaffargarh'),
            ('Taunsa Sharif, Dera Ghazi Khan', 'Dera Ghazi Khan'),
            ('Rajanpur City, District Rajanpur', 'Rajanpur'),
            ('Liaquatpur, District Rahim Yar Khan', 'Liaquatpur'),
        ]

        with transaction.atomic():
            ali_hall, _ = Hostel.objects.get_or_create(
                name="Ali Hall (Boys Hostel), IUB",
                defaults={
                    'gender_category': Hostel.GenderCategory.BOYS,
                    'total_floors': 3,
                    'address': 'Baghdad-ul-Jadeed Campus, The Islamia University of Bahawalpur, Bahawalpur, Punjab, Pakistan',
                    'contact_number': '+92-62-9255501',
                    'description': 'Premier boys residential hall at Baghdad-ul-Jadeed Campus, IUB, containing 300 rooms with 600 student bed capacity.'
                }
            )

            # 3 Blocks for Ali Hall
            block_quaid, _ = Block.objects.get_or_create(
                hostel=ali_hall,
                block_name="Quaid Block (Block A)",
                defaults={'description': 'Ground Floor: Rooms 1 to 100 (Reserved for Special Needs / Medical Quota Scholars)'}
            )
            block_iqbal, _ = Block.objects.get_or_create(
                hostel=ali_hall,
                block_name="Iqbal Block (Block B)",
                defaults={'description': '1st Floor: Rooms 101 to 200 (Regular Student Residents)'}
            )
            block_sir_syed, _ = Block.objects.get_or_create(
                hostel=ali_hall,
                block_name="Sir Syed Block (Block C)",
                defaults={'description': '2nd Floor: Rooms 201 to 300 (Regular Student Residents)'}
            )

            # Clear legacy rooms outside 1-300 or existing allotments
            Allotment.objects.filter(room__block__hostel=ali_hall).delete()
            Bed.objects.filter(room__block__hostel=ali_hall).delete()
            Room.objects.filter(block__hostel=ali_hall).delete()

            # 1. Create exactly 300 Rooms and 600 Beds (Bed-A, Bed-B)
            # Rooms 1 to 100: Ground Floor (Floor 1), Special Quota
            # Rooms 101 to 200: 1st Floor (Floor 2), Regular Quota
            # Rooms 201 to 300: 2nd Floor (Floor 3), Regular Quota
            blocks_plan = [
                (block_quaid, 1, 100, 1, True),
                (block_iqbal, 101, 200, 2, False),
                (block_sir_syed, 201, 300, 3, False),
            ]

            all_rooms = []
            all_beds = []
            rooms_map = {}

            for block, start_r, end_r, floor_num, is_special in blocks_plan:
                for r_num in range(start_r, end_r + 1):
                    r_str = str(r_num)
                    room = Room(
                        block=block,
                        room_number=r_str,
                        floor=floor_num,
                        room_type=Room.RoomType.DOUBLE,
                        capacity=2,
                        price_per_bed=Decimal('5000.00'),
                        maintenance_status=Room.MaintenanceStatus.OPERATIONAL,
                        is_special_quota=is_special
                    )
                    all_rooms.append(room)

            Room.objects.bulk_create(all_rooms)

            # Retrieve created rooms to have database IDs
            created_rooms = Room.objects.filter(block__hostel=ali_hall).select_related('block')
            for r in created_rooms:
                rooms_map[int(r.room_number)] = r
                all_beds.append(Bed(room=r, bed_code="Bed-A", status=Bed.Status.AVAILABLE))
                all_beds.append(Bed(room=r, bed_code="Bed-B", status=Bed.Status.AVAILABLE))

            Bed.objects.bulk_create(all_beds)

            # Retrieve created beds
            created_beds = Bed.objects.filter(room__block__hostel=ali_hall).select_related('room')
            beds_map = {}  # (room_number, 'Bed-A' or 'Bed-B') -> Bed
            for b in created_beds:
                beds_map[(int(b.room.room_number), b.bed_code)] = b

            self.stdout.write(self.style.SUCCESS(f"Created {len(rooms_map)} Rooms and {len(beds_map)} Beds successfully."))

            # 2. Determine Vacant Beds (Exactly 20 spaces vacant)
            # Ground Floor Special Quota (Rooms 1-100 = 200 beds):
            # - 4 beds vacant: Room 99 (Bed-A, Bed-B), Room 100 (Bed-A, Bed-B)
            # 1st Floor Regular (Rooms 101-200 = 200 beds):
            # - 8 beds vacant: Room 195 Bed-B, Room 196 Bed-B, Room 197 Bed-B, Room 198 Bed-B, Room 199 (A, B), Room 200 (A, B)
            # 2nd Floor Regular (Rooms 201-300 = 200 beds):
            # - 8 beds vacant: Room 295 Bed-B, Room 296 Bed-B, Room 297 Bed-B, Room 298 Bed-B, Room 299 (A, B), Room 300 (A, B)
            # Total vacant = 4 + 8 + 8 = 20 vacant spaces!
            vacant_beds_keys = {
                (99, 'Bed-A'), (99, 'Bed-B'), (100, 'Bed-A'), (100, 'Bed-B'),
                (195, 'Bed-B'), (196, 'Bed-B'), (197, 'Bed-B'), (198, 'Bed-B'), (199, 'Bed-A'), (199, 'Bed-B'), (200, 'Bed-A'), (200, 'Bed-B'),
                (295, 'Bed-B'), (296, 'Bed-B'), (297, 'Bed-B'), (298, 'Bed-B'), (299, 'Bed-A'), (299, 'Bed-B'), (300, 'Bed-A'), (300, 'Bed-B'),
            }

            beds_to_allocate = []
            for r_num in range(1, 301):
                for b_code in ['Bed-A', 'Bed-B']:
                    key = (r_num, b_code)
                    if key not in vacant_beds_keys:
                        beds_to_allocate.append(beds_map[key])

            total_allocated_beds = len(beds_to_allocate)
            self.stdout.write(self.style.NOTICE(f"Total beds to occupy: {total_allocated_beds} (Leaving exactly {len(vacant_beds_keys)} vacant spaces)"))

            # 3. Create 580 Student Accounts with full realistic details
            # Specific named students for demo
            lead_students = [
                ('student_ali', 'Ali', 'Hassan', '+92-301-2345678', '5440166878999', 'FA22-BCS-001', 'Computer Science', 5, 'Street 4, Muslim Town, Multan', '+92-300-1122334 (Father: M. Hassan)'),
                ('student_rizwan', 'Rizwan', 'Ahmed', '+92-302-8877665', '31202-7654321-3', 'FA22-BSE-002', 'Software Engineering', 5, 'House 14, Model Town, Bahawalpur', '+92-301-9988776 (Father: Ahmed Yar)'),
                ('student_usman', 'Usman', 'Tariq', '+92-302-3456789', '31202-2345678-3', 'FA22-BSE-089', 'Software Engineering', 5, 'House 12, Gulshan-e-Iqbal, Rahim Yar Khan', '+92-301-5566778 (Father: Tariq Mehmood)'),
                ('student_bilal', 'Bilal', 'Ahmed', '+92-303-4567890', '31202-3456789-5', 'SP23-BIT-018', 'Information Technology', 4, 'Ward No. 7, Model Town, Ahmedpur East', '+92-302-6677889 (Brother: Zohaib)'),
                ('student_hamza', 'Hamza', 'Khan', '+92-304-5678901', '31202-4567890-7', 'FA21-BEE-032', 'Electrical Engineering', 7, 'Colony Road, Hasilpur, District Bahawalpur', '+92-303-7788990 (Father: Abdul Rehman)'),
                ('student_tariq', 'Tariq', 'Mehmood', '+92-305-6789012', '31202-5678901-9', 'FA23-BCE-019', 'Civil Engineering', 3, 'Circular Road, Lodhran', '+92-304-8899001 (Father: M. Tariq)'),
                ('student_zain', 'Zain', 'Malik', '+92-306-7890123', '31202-6789012-1', 'FA24-BBA-112', 'Management Sciences', 1, 'Airport Road, Bahawalpur', '+92-305-9900112 (Father: Malik Naveed)'),
                ('student_farooq', 'Farooq', 'Siddiqui', '+92-307-8901234', '31202-7890123-3', 'SP22-CHM-044', 'Chemistry', 6, 'Jampur Road, Dera Ghazi Khan', '+92-306-1122445 (Father: Farooq Sr.)'),
            ]

            # Clear old student users except staff
            User.objects.filter(role=User.Role.STUDENT).delete()

            student_objs = []
            now_dt = timezone.now()

            # Pre-generate hashed password for speed
            temp_user = User(username='temp')
            temp_user.set_password('student123')
            hashed_pwd = temp_user.password

            for idx in range(total_allocated_beds):
                if idx < len(lead_students):
                    u_name, f_name, l_name, phone, cnic, reg_no, dept, sem, addr, emerg = lead_students[idx]
                else:
                    fn = first_names[idx % len(first_names)]
                    ln = last_names[(idx // len(first_names)) % len(last_names)]
                    f_name = fn
                    l_name = ln
                    u_name = f"student_{idx + 1}"
                    phone = f"+92-30{(idx % 10)}-{1000000 + (idx * 37) % 8999999}"
                    cnic = f"31202-{1000000 + (idx * 19) % 8999999:07d}-{(idx % 9) + 1}"
                    dept, dept_code = departments_list[idx % len(departments_list)]
                    sem = (idx % 8) + 1
                    term = "FA" if (idx % 2 == 0) else "SP"
                    year = 21 + (idx % 4)
                    reg_no = f"{term}{year}-{dept_code}-{100 + idx:03d}"
                    addr_str, city = cities_addresses[idx % len(cities_addresses)]
                    addr = addr_str
                    emerg = f"+92-30{(idx + 3) % 10}-{2000000 + (idx * 43) % 7999999} (Guardian: {ln})"

                user = User(
                    username=u_name,
                    first_name=f_name,
                    last_name=l_name,
                    email=f"{f_name.lower()}.{l_name.lower()}{idx+1}@student.iub.edu.pk",
                    phone_number=phone,
                    cnic=cnic,
                    cnic_or_id=cnic,
                    registration_no=reg_no,
                    department=dept,
                    semester=sem,
                    address=addr,
                    emergency_contact=emerg,
                    role=User.Role.STUDENT,
                    application_status=User.ApplicationStatus.ALLOCATED,
                    application_notes='Verified and allocated bed in Ali Hall Hostel, IUB.',
                    application_date=now_dt - timedelta(days=60),
                    password=hashed_pwd,
                )
                student_objs.append(user)

            User.objects.bulk_create(student_objs)
            self.stdout.write(self.style.SUCCESS(f"Created {len(student_objs)} Student resident accounts."))

            # Retrieve created student users
            saved_students = list(User.objects.filter(role=User.Role.STUDENT).order_by('id'))

            # 4. Create Allotments
            allotment_objs = []
            beds_to_update = []

            for i in range(total_allocated_beds):
                st = saved_students[i]
                b = beds_to_allocate[i]
                b.status = Bed.Status.OCCUPIED
                beds_to_update.append(b)

                allotment = Allotment(
                    student=st,
                    room=b.room,
                    bed=b,
                    allotment_date=timezone.now().date() - timedelta(days=45),
                    is_active=True,
                    remarks=f"Regular 2026 Residency Allotment - {'Special Quota' if b.room.is_special_quota else 'Regular Quota'}"
                )
                allotment_objs.append(allotment)

            Bed.objects.bulk_update(beds_to_update, ['status'])
            Allotment.objects.bulk_create(allotment_objs)

            self.stdout.write(self.style.SUCCESS(f"Allocated {len(allotment_objs)} beds successfully!"))

            # Summary Verification
            total_r = Room.objects.filter(block__hostel=ali_hall).count()
            total_b = Bed.objects.filter(room__block__hostel=ali_hall).count()
            occ_b = Bed.objects.filter(room__block__hostel=ali_hall, status=Bed.Status.OCCUPIED).count()
            vac_b = Bed.objects.filter(room__block__hostel=ali_hall, status=Bed.Status.AVAILABLE).count()

            sp_r = Room.objects.filter(block__hostel=ali_hall, is_special_quota=True).count()
            sp_occ = Bed.objects.filter(room__block__hostel=ali_hall, room__is_special_quota=True, status=Bed.Status.OCCUPIED).count()
            sp_vac = Bed.objects.filter(room__block__hostel=ali_hall, room__is_special_quota=True, status=Bed.Status.AVAILABLE).count()

            reg_r = Room.objects.filter(block__hostel=ali_hall, is_special_quota=False).count()
            reg_occ = Bed.objects.filter(room__block__hostel=ali_hall, room__is_special_quota=False, status=Bed.Status.OCCUPIED).count()
            reg_vac = Bed.objects.filter(room__block__hostel=ali_hall, room__is_special_quota=False, status=Bed.Status.AVAILABLE).count()

        self.stdout.write(self.style.SUCCESS("========================================================="))
        self.stdout.write(self.style.SUCCESS(f"Ali Hall Setup Complete!"))
        self.stdout.write(self.style.SUCCESS(f"Total Rooms: {total_r} (Rooms 1 to 300)"))
        self.stdout.write(self.style.SUCCESS(f"  - Ground Floor Special Quota: {sp_r} Rooms (Rooms 1-100) -> {sp_occ} Occupied, {sp_vac} Vacant"))
        self.stdout.write(self.style.SUCCESS(f"  - Upper Floors Regular Quota: {reg_r} Rooms (Rooms 101-300) -> {reg_occ} Occupied, {reg_vac} Vacant"))
        self.stdout.write(self.style.SUCCESS(f"Total Bed Capacity: {total_b} Beds"))
        self.stdout.write(self.style.SUCCESS(f"  - Occupied Beds: {occ_b}"))
        self.stdout.write(self.style.SUCCESS(f"  - EXACTLY Vacant Beds: {vac_b}"))
        self.stdout.write(self.style.SUCCESS("========================================================="))
