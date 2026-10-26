import uuid
from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Custom user manager supporting roles and phone numbers."""
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be provided")
        email = self.normalize_email(email) if email else ''
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Role-Based Custom User Model.
    Supports SuperAdmin/Admin, Chief Warden, Warden, and Student roles with academic metadata and document uploads.
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'System Administrator'
        CHIEF_WARDEN = 'CHIEF_WARDEN', 'Chief Warden'
        WARDEN = 'WARDEN', 'Hostel Warden / Staff'
        STUDENT = 'STUDENT', 'Student / Resident'

    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    class ApplicationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved for Allotment'
        REJECTED = 'REJECTED', 'Application Rejected'
        ALLOCATED = 'ALLOCATED', 'Room Allocated'

    role = models.CharField(
        max_length=15,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="Designates the user's operational role and authorization level."
    )
    phone_number = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    cnic = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Student CNIC Number",
        help_text="13-digit Pakistani CNIC e.g. 5440166878999 or 54401-6687899-9"
    )
    cnic_or_id = models.CharField(max_length=30, blank=True, verbose_name="CNIC / IUB Roll Number", help_text="e.g. FA22-BCS-045 or CNIC")
    registration_no = models.CharField(max_length=50, blank=True, verbose_name="University Reg / Roll No", help_text="e.g. FA22-BCS-045")
    department = models.CharField(max_length=120, blank=True, help_text="e.g. Computer Science, Software Engineering")
    semester = models.CharField(max_length=30, blank=True, help_text="e.g. 1st, 2nd, 5th, 8th")
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    emergency_contact = models.CharField(max_length=50, blank=True, help_text="Guardian or Emergency Contact")
    address = models.TextField(blank=True, help_text="Permanent residential address")

    # Student Hostel Application & Document Verification
    application_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        help_text="Status of hostel admission application"
    )
    application_date = models.DateTimeField(default=timezone.now)
    application_notes = models.TextField(blank=True, help_text="Reviewer or applicant remarks")
    reviewed_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_student_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Document Uploads
    document_cnic = models.FileField(
        upload_to='student_docs/',
        blank=True,
        null=True,
        verbose_name="CNIC / B-Form Document",
        help_text="Scanned copy of CNIC or B-Form"
    )
    document_admission_slip = models.FileField(
        upload_to='student_docs/',
        blank=True,
        null=True,
        verbose_name="University Admission / Fee Challan",
        help_text="Official university admission letter or paid fee slip"
    )
    document_other = models.FileField(
        upload_to='student_docs/',
        blank=True,
        null=True,
        verbose_name="Additional Supporting Document",
        help_text="Domicile or guardian undertaking"
    )

    # Warden Specific Assignment & Granular Permissions
    assigned_hostel = models.ForeignKey(
        'Hostel',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_wardens'
    )
    assigned_block = models.ForeignKey(
        'Block',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_wardens'
    )
    warden_designation = models.CharField(max_length=100, blank=True, default='Hostel Warden')
    can_manage_allocations = models.BooleanField(default=True)
    can_manage_complaints = models.BooleanField(default=True)
    can_manage_gatepasses = models.BooleanField(default=True)
    can_manage_room_changes = models.BooleanField(default=True)

    objects = CustomUserManager()

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_chief_warden_user(self):
        return self.role == self.Role.CHIEF_WARDEN

    @property
    def is_warden_user(self):
        return self.role == self.Role.WARDEN

    @property
    def is_student_user(self):
        return self.role == self.Role.STUDENT

    @property
    def is_staff_or_admin(self):
        return self.is_admin_user or self.is_chief_warden_user or self.is_warden_user

    @property
    def clean_cnic(self):
        """Returns the numeric digits of CNIC without dashes or spaces."""
        raw = self.cnic or self.cnic_or_id or ""
        digits = "".join(ch for ch in str(raw) if ch.isdigit())
        return digits

    @property
    def formatted_cnic(self):
        """Returns standard 13-digit Pakistani CNIC formatted as XXXXX-XXXXXXX-X."""
        digits = self.clean_cnic
        if len(digits) == 13:
            return f"{digits[:5]}-{digits[5:12]}-{digits[12]}"
        return self.cnic or self.cnic_or_id or ""

    def save(self, *args, **kwargs):
        if self.cnic and not self.cnic_or_id:
            self.cnic_or_id = self.cnic
        elif self.cnic_or_id and not self.cnic:
            digits = "".join(ch for ch in str(self.cnic_or_id) if ch.isdigit())
            if len(digits) >= 12:
                self.cnic = self.cnic_or_id
        super().save(*args, **kwargs)

    @property
    def active_allotment(self):
        """Returns the current active allotment for this student if any."""
        if not self.is_student_user:
            return None
        return self.allotments.filter(is_active=True).select_related('room', 'bed', 'room__block', 'room__block__hostel').first()

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()

    @property
    def initials(self):
        full = self.get_full_name() or self.username
        parts = full.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        return "ST"

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        reg = f" [{self.registration_no or self.cnic_or_id}]" if (self.registration_no or self.cnic_or_id) else ""
        return f"{display}{reg} ({self.get_role_display()})"


class Hostel(models.Model):
    """Hostel property/building details."""
    class GenderCategory(models.TextChoices):
        BOYS = 'BOYS', 'Boys Hostel'
        GIRLS = 'GIRLS', 'Girls Hostel'
        COED = 'COED', 'Co-Ed Hostel'

    name = models.CharField(max_length=120, unique=True)
    gender_category = models.CharField(max_length=10, choices=GenderCategory.choices, default=GenderCategory.BOYS)
    total_floors = models.PositiveIntegerField(default=1)
    address = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_gender_category_display()})"

    @property
    def total_rooms_count(self):
        return Room.objects.filter(block__hostel=self).count()

    @property
    def total_beds_count(self):
        return Bed.objects.filter(room__block__hostel=self).count()

    @property
    def occupied_beds_count(self):
        return Bed.objects.filter(room__block__hostel=self, status=Bed.Status.OCCUPIED).count()

    @property
    def available_beds_count(self):
        return Bed.objects.filter(room__block__hostel=self, status=Bed.Status.AVAILABLE).count()

    @property
    def maintenance_beds_count(self):
        return Bed.objects.filter(room__block__hostel=self, status=Bed.Status.MAINTENANCE).count()

    @property
    def occupancy_rate(self):
        total = self.total_beds_count
        if total == 0:
            return 0
        return round((self.occupied_beds_count / total) * 100, 1)


class Block(models.Model):
    """Hostel Blocks / Wings (e.g. Quaid Block, Iqbal Block, Sir Syed Block)."""
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='blocks')
    block_name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('hostel', 'block_name')
        ordering = ['block_name']

    def __str__(self):
        return f"{self.hostel.name} - {self.block_name}"

    @property
    def total_rooms_count(self):
        return self.rooms.count()

    @property
    def total_beds_count(self):
        return Bed.objects.filter(room__block=self).count()

    @property
    def occupied_beds_count(self):
        return Bed.objects.filter(room__block=self, status=Bed.Status.OCCUPIED).count()

    @property
    def available_beds_count(self):
        return Bed.objects.filter(room__block=self, status=Bed.Status.AVAILABLE).count()


class Room(models.Model):
    """
    Hostel Rooms.
    Standardized capacity: 2 students per room (Double room, 2 beds).
    """
    class RoomType(models.TextChoices):
        SINGLE = 'SINGLE', 'Single Room (1 Bed)'
        DOUBLE = 'DOUBLE', 'Double Room (2 Beds)'
        TRIPLE = 'TRIPLE', 'Triple Room (3 Beds)'
        QUAD = 'QUAD', 'Quad Room (4 Beds)'

    class MaintenanceStatus(models.TextChoices):
        OPERATIONAL = 'OPERATIONAL', 'Operational'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'

    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    floor = models.PositiveIntegerField(default=1)
    room_type = models.CharField(max_length=10, choices=RoomType.choices, default=RoomType.DOUBLE)
    capacity = models.PositiveIntegerField(default=2)
    price_per_bed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000.00'), help_text="Monthly price per bed in PKR (Rs.)")
    maintenance_status = models.CharField(max_length=20, choices=MaintenanceStatus.choices, default=MaintenanceStatus.OPERATIONAL)
    is_special_quota = models.BooleanField(
        default=False,
        help_text="Reserved for special students (disabled/medical quota) on Ground Floor (Rooms 1-100)"
    )

    class Meta:
        unique_together = ('block', 'room_number')
        ordering = ['floor', 'room_number']

    def __str__(self):
        return f"Room {self.room_number} ({self.block.block_name})"

    @property
    def is_special_reserved(self):
        """Returns True if this room is reserved for special students (Rooms 1-100 on Ground Floor)."""
        if self.is_special_quota:
            return True
        try:
            r_num = int(self.room_number)
            return (1 <= r_num <= 100) and (self.floor == 1)
        except (ValueError, TypeError):
            return False

    @property
    def quota_category_display(self):
        if self.is_special_reserved:
            return "Special Students (Ground Floor)"
        return "Regular Students"

    @property
    def available_beds(self):
        return self.beds.filter(status=Bed.Status.AVAILABLE)

    @property
    def available_beds_count(self):
        return self.available_beds.count()

    @property
    def occupied_beds_count(self):
        return self.beds.filter(status=Bed.Status.OCCUPIED).count()

    @property
    def is_full(self):
        return self.available_beds_count == 0

    @property
    def is_operational(self):
        return self.maintenance_status == self.MaintenanceStatus.OPERATIONAL

    @property
    def occupancy_status(self):
        if self.maintenance_status == self.MaintenanceStatus.MAINTENANCE:
            return 'MAINTENANCE'
        avail = self.available_beds_count
        if avail == 0:
            return 'FULLY_OCCUPIED'
        elif avail == self.capacity:
            return 'AVAILABLE'
        else:
            return 'PARTIALLY_OCCUPIED'

    @property
    def occupancy_status_display(self):
        mapping = {
            'MAINTENANCE': 'Under Maintenance',
            'FULLY_OCCUPIED': 'Fully Occupied',
            'AVAILABLE': 'Available',
            'PARTIALLY_OCCUPIED': 'Partially Occupied'
        }
        return mapping.get(self.occupancy_status, 'Unknown')

    @property
    def assigned_students(self):
        """Returns the list of student users currently allotted to this room."""
        return [a.student for a in self.allotments.filter(is_active=True).select_related('student')]


class Bed(models.Model):
    """Individual bed unit inside a room (e.g. Bed-A, Bed-B)."""
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_code = models.CharField(max_length=20, help_text="e.g. Bed-A, Bed-B")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.AVAILABLE)

    class Meta:
        unique_together = ('room', 'bed_code')
        ordering = ['bed_code']

    def __str__(self):
        return f"{self.room} - {self.bed_code} [{self.get_status_display()}]"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def current_allotment(self):
        return self.allotments.filter(is_active=True).first()

    @property
    def current_student(self):
        allotment = self.current_allotment
        return allotment.student if allotment else None


class Allotment(models.Model):
    """
    Bed Allotment Record with strict Zero Double-Booking validation and atomic updates.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='allotments',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='allotments')
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='allotments')
    allotment_date = models.DateField(default=timezone.now)
    vacate_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Indicates current active residency.")
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['bed'],
                condition=models.Q(is_active=True),
                name='unique_active_bed_allocation'
            ),
            models.UniqueConstraint(
                fields=['student'],
                condition=models.Q(is_active=True),
                name='unique_active_student_allocation'
            ),
        ]

    def __str__(self):
        return f"Allotment: {self.student.username} -> {self.bed} ({'Active' if self.is_active else 'Vacated'})"

    def clean(self):
        super().clean()
        if self.student and self.student.role != User.Role.STUDENT:
            raise ValidationError({'student': "Only users with the 'Student' role can be allocated beds."})

        # Ensure bed belongs to the selected room
        if self.bed and self.room and self.bed.room_id != self.room_id:
            raise ValidationError({'bed': "The selected bed does not belong to the selected room."})

        if self.is_active:
            # Check for existing active allotment for this bed
            existing_bed_allotment = Allotment.objects.filter(
                bed=self.bed,
                is_active=True
            )
            if self.pk:
                existing_bed_allotment = existing_bed_allotment.exclude(pk=self.pk)

            if existing_bed_allotment.exists():
                occupied_by = existing_bed_allotment.first().student.get_full_name() or existing_bed_allotment.first().student.username
                raise ValidationError({
                    'bed': f"Bed {self.bed.bed_code} is already allocated to {occupied_by}. Zero double-booking enforced."
                })

            # Check if student already has another active allotment
            existing_student_allotment = Allotment.objects.filter(
                student=self.student,
                is_active=True
            )
            if self.pk:
                existing_student_allotment = existing_student_allotment.exclude(pk=self.pk)

            if existing_student_allotment.exists():
                current_bed = existing_student_allotment.first().bed
                raise ValidationError({
                    'student': f"Student {self.student.username} already holds an active allotment at {current_bed}. Please vacate first."
                })

            # Bed status check
            if not self.pk and self.bed.status == Bed.Status.MAINTENANCE:
                raise ValidationError({'bed': "This bed is currently under maintenance and cannot be allocated."})

            # Capacity check (max 2 students per room)
            current_occupants = Allotment.objects.filter(room=self.room, is_active=True)
            if self.pk:
                current_occupants = current_occupants.exclude(pk=self.pk)
            if current_occupants.count() >= self.room.capacity:
                raise ValidationError({'room': f"Room {self.room.room_number} is already at full capacity ({self.room.capacity} students)."})

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            # Sync bed status
            if self.is_active:
                if self.bed.status != Bed.Status.OCCUPIED:
                    self.bed.status = Bed.Status.OCCUPIED
                    self.bed.save(update_fields=['status'])
                # Also mark student's application_status as ALLOCATED
                if self.student.application_status != User.ApplicationStatus.ALLOCATED:
                    self.student.application_status = User.ApplicationStatus.ALLOCATED
                    self.student.save(update_fields=['application_status'])
            else:
                # If allotment is deactivated or vacated, release bed
                has_active = Allotment.objects.filter(bed=self.bed, is_active=True).exclude(pk=self.pk).exists()
                if not has_active:
                    self.bed.status = Bed.Status.AVAILABLE
                    self.bed.save(update_fields=['status'])

    def vacate(self, remarks=None):
        """Helper method to vacate an allotment safely."""
        with transaction.atomic():
            self.is_active = False
            self.vacate_date = timezone.now().date()
            if remarks:
                self.remarks = f"{self.remarks}\n[Vacated on {self.vacate_date}]: {remarks}".strip()
            self.save()
            self.bed.status = Bed.Status.AVAILABLE
            self.bed.save(update_fields=['status'])


class FeeVoucher(models.Model):
    """
    Student Fee Voucher and Payment tracking.
    """
    class FeeType(models.TextChoices):
        HOSTEL_FEE = 'HOSTEL_FEE', 'Hostel Fee (Rent)'
        MESS_FEE = 'MESS_FEE', 'Mess Fee'
        SECURITY_DEPOSIT = 'SECURITY_DEPOSIT', 'Security Deposit'
        UTILITY = 'UTILITY', 'Utility & Maintenance'
        OTHER = 'OTHER', 'Other / Fines'

    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PENDING_VERIFICATION = 'PENDING_VERIFICATION', 'Pending Verification'
        PAID = 'PAID', 'Paid'
        REJECTED = 'REJECTED', 'Rejected'
        OVERDUE = 'OVERDUE', 'Overdue'

    voucher_code = models.CharField(max_length=36, unique=True, editable=False)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fee_vouchers',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    fee_type = models.CharField(max_length=20, choices=FeeType.choices, default=FeeType.HOSTEL_FEE)
    billing_month = models.CharField(max_length=30, blank=True, help_text="e.g. October 2026 or Fall 2026")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.UNPAID)
    
    # Payment verification fields
    payment_method = models.CharField(max_length=50, blank=True, help_text="e.g. Bank Transfer, Online, Cash")
    payment_proof = models.FileField(upload_to='fee_proofs/', blank=True, null=True, help_text="Receipt image or PDF")
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Bank Ref / Transaction ID")
    payment_date = models.DateField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_vouchers'
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.voucher_code:
            self.voucher_code = f"VCH-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        
        if self.status == self.Status.UNPAID and self.due_date < timezone.now().date():
            self.status = self.Status.OVERDUE

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.voucher_code} - {self.student.username} (Rs. {self.amount}) [{self.get_status_display()}]"

    @property
    def is_defaulter(self):
        return self.status in [self.Status.UNPAID, self.Status.OVERDUE] and self.due_date < timezone.now().date()

    @property
    def is_file_image(self):
        if not self.payment_proof:
            return False
        ext = self.payment_proof.name.lower().split('.')[-1]
        return ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']

    @property
    def is_file_pdf(self):
        if not self.payment_proof:
            return False
        return self.payment_proof.name.lower().endswith('.pdf')


class Complaint(models.Model):
    """
    Student Maintenance and Incident Complaints with all 11 standardized categories.
    """
    class Category(models.TextChoices):
        ROOM_MAINTENANCE = 'ROOM_MAINTENANCE', 'Room maintenance'
        ELECTRICAL = 'ELECTRICAL', 'Electrical problems'
        WATER = 'WATER', 'Water supply'
        BATHROOM = 'BATHROOM', 'Bathroom problems'
        CLEANLINESS = 'CLEANLINESS', 'Cleanliness'
        FURNITURE = 'FURNITURE', 'Furniture damage'
        INTERNET = 'INTERNET', 'Internet and Wi-Fi'
        ROOMMATE = 'ROOMMATE', 'Roommate issues'
        FOOD = 'FOOD', 'Food quality'
        SECURITY = 'SECURITY', 'Security concerns'
        OTHER = 'OTHER', 'Other complaints'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        REJECTED = 'REJECTED', 'Rejected'

    complaint_ref = models.CharField(max_length=36, blank=True, default='', editable=False)
    ticket_number = models.CharField(max_length=36, unique=True, editable=False)  # Preserved for backward compatibility
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='complaints',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.ROOM_MAINTENANCE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    room_number = models.CharField(max_length=50, blank=True, help_text="Room number where the problem is located")
    priority = models.CharField(max_length=15, choices=Priority.choices, default=Priority.MEDIUM)
    photo = models.ImageField(upload_to='complaints/', blank=True, null=True, help_text="Optional photograph")
    supporting_attachment = models.FileField(upload_to='complaints/', blank=True, null=True, help_text="Optional supporting attachment")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    
    # Assignment & Resolution details
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        help_text="Warden or maintenance staff assigned to investigate"
    )
    warden_remarks = models.TextField(blank=True, verbose_name="Staff / Warden Resolution Remarks")
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_complaints'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.complaint_ref:
            code = f"CMP-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
            self.complaint_ref = code
            if not self.ticket_number:
                self.ticket_number = code
        elif not self.ticket_number:
            self.ticket_number = self.complaint_ref

        if self.status == self.Status.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_ref} - {self.title} [{self.get_status_display()}]"


class RoomChangeRequest(models.Model):
    """
    Student Room-Change Request with multi-tier Warden recommendation and Admin approval workflow.
    """
    class ReasonCategory(models.TextChoices):
        ROOMMATE = 'ROOMMATE', 'Roommate conflicts'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance problems'
        NOISE = 'NOISE', 'Excessive noise / study disturbance'
        SAFETY = 'SAFETY', 'Personal safety concerns'
        MEDICAL = 'MEDICAL', 'Medical / ground floor requirement'
        OTHER = 'OTHER', 'Other genuine difficulties'

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review by Warden'
        WARDEN_RECOMMENDED = 'WARDEN_RECOMMENDED', 'Recommended by Warden'
        WARDEN_NOT_RECOMMENDED = 'WARDEN_NOT_RECOMMENDED', 'Not Recommended by Warden'
        APPROVED = 'APPROVED', 'Approved by Admin'
        REJECTED = 'REJECTED', 'Rejected'
        COMPLETED = 'COMPLETED', 'Transfer Completed'

    class WardenRecommendation(models.TextChoices):
        PENDING = 'PENDING', 'Pending Assessment'
        RECOMMENDED = 'RECOMMENDED', 'Recommended for Transfer'
        NOT_RECOMMENDED = 'NOT_RECOMMENDED', 'Not Recommended'

    request_code = models.CharField(max_length=36, unique=True, editable=False)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='room_change_requests',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    current_allotment = models.ForeignKey(Allotment, on_delete=models.CASCADE, related_name='room_change_requests')
    current_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='change_requests_from')
    current_bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='change_requests_from')
    reason_category = models.CharField(max_length=30, choices=ReasonCategory.choices, default=ReasonCategory.ROOMMATE)
    detailed_explanation = models.TextField(help_text="Explain why you require a room change.")
    preferred_room = models.ForeignKey(
        Room,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='change_requests_to',
        help_text="Optional preferred room number or block"
    )
    supporting_document = models.FileField(upload_to='room_change_docs/', blank=True, null=True, help_text="Medical certificate or supporting proof")
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.SUBMITTED)

    # Multi-tier Review Workflow
    warden_recommendation = models.CharField(
        max_length=20,
        choices=WardenRecommendation.choices,
        default=WardenRecommendation.PENDING
    )
    warden_remarks = models.TextField(blank=True, help_text="Warden's field investigation remarks and recommendation.")
    reviewed_by_warden = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='warden_reviewed_transfers'
    )
    admin_remarks = models.TextField(blank=True, help_text="Chief Warden / Administrator decision notes.")
    reviewed_by_admin = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='admin_reviewed_transfers'
    )
    
    # Newly Assigned Target
    new_room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name='new_room_allocations')
    new_bed = models.ForeignKey(Bed, null=True, blank=True, on_delete=models.SET_NULL, related_name='new_bed_allocations')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.request_code:
            self.request_code = f"RCR-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_code} - {self.student.username} (Room {self.current_room.room_number}) [{self.get_status_display()}]"


class Notification(models.Model):
    """
    System Notification model for Students, Wardens, and Administrators.
    """
    class Type(models.TextChoices):
        APPLICATION = 'APPLICATION', 'Hostel Application'
        ALLOCATION = 'ALLOCATION', 'Room Allocation'
        COMPLAINT = 'COMPLAINT', 'Maintenance Complaint'
        ROOM_CHANGE = 'ROOM_CHANGE', 'Room Change Request'
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Hostel Notice'
        GENERAL = 'GENERAL', 'System Alert'

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=Type.choices, default=Type.GENERAL)
    link_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title} ({'Read' if self.is_read else 'Unread'})"

    @classmethod
    def send(cls, recipient, title, message, notification_type=Type.GENERAL, link_url=''):
        """Convenience method to dispatch a notification."""
        return cls.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url
        )


class HostelAnnouncement(models.Model):
    """
    Hostel Notices and Announcements broadcast board.
    """
    class Category(models.TextChoices):
        GENERAL = 'GENERAL', 'General Notice'
        TIMINGS = 'TIMINGS', 'Hostel Timings / Curfew'
        DISCIPLINE = 'DISCIPLINE', 'Discipline & Rules'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance Shutdown'
        FEES = 'FEES', 'Fee Notice'
        HOLIDAY = 'HOLIDAY', 'Holidays / Vacations'

    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        IMPORTANT = 'IMPORTANT', 'Important'
        URGENT = 'URGENT', 'Urgent Alert'

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)
    priority = models.CharField(max_length=15, choices=Priority.choices, default=Priority.NORMAL)
    content = models.TextField()
    published_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='published_announcements')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"


class GatePass(models.Model):
    """
    Student Gate Pass and Leave Authorizations.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        COMPLETED = 'COMPLETED', 'Returned / Closed'

    pass_code = models.CharField(max_length=36, unique=True, editable=False)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gate_passes',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    reason = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    emergency_contact = models.CharField(max_length=50)
    leave_date = models.DateTimeField()
    return_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_gate_passes'
    )
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pass_code:
            self.pass_code = f"GP-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pass_code} - {self.student.username} [{self.get_status_display()}]"


class MessSchedule(models.Model):
    """
    Weekly Mess Food Timetable.
    """
    class DayOfWeek(models.TextChoices):
        MONDAY = 'MONDAY', 'Monday'
        TUESDAY = 'TUESDAY', 'Tuesday'
        WEDNESDAY = 'WEDNESDAY', 'Wednesday'
        THURSDAY = 'THURSDAY', 'Thursday'
        FRIDAY = 'FRIDAY', 'Friday'
        SATURDAY = 'SATURDAY', 'Saturday'
        SUNDAY = 'SUNDAY', 'Sunday'

    class MealType(models.TextChoices):
        BREAKFAST = 'BREAKFAST', 'Breakfast'
        LUNCH = 'LUNCH', 'Lunch'
        SNACKS = 'SNACKS', 'Evening Snacks'
        DINNER = 'DINNER', 'Dinner'

    day_of_week = models.CharField(max_length=15, choices=DayOfWeek.choices)
    meal_type = models.CharField(max_length=15, choices=MealType.choices)
    menu_description = models.TextField(help_text="Items served (e.g. Paratha, Omelet, Tea / Biryani, Raita)")
    timing = models.CharField(max_length=100, blank=True, help_text="e.g. 7:30 AM - 9:30 AM")
    special_note = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('day_of_week', 'meal_type')
        ordering = ['day_of_week', 'meal_type']

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.get_meal_type_display()}"
