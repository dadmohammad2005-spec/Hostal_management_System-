from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class StudentProfile(models.Model):
    """
    Complete Student Mess Profile with photo, academics, room, contact, and fee settings.
    """
    class MessStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active Member'
        INACTIVE = 'INACTIVE', 'Inactive'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    class Semester(models.TextChoices):
        SEM_1 = '1st', '1st Semester'
        SEM_2 = '2nd', '2nd Semester'
        SEM_3 = '3rd', '3rd Semester'
        SEM_4 = '4th', '4th Semester'
        SEM_5 = '5th', '5th Semester'
        SEM_6 = '6th', '6th Semester'
        SEM_7 = '7th', '7th Semester'
        SEM_8 = '8th', '8th Semester'
        POSTGRAD = 'Postgraduate', 'Postgraduate / MS / PhD'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )
    student_id = models.CharField(max_length=50, unique=True, verbose_name="Student ID / Roll No", help_text="e.g. FA22-BCS-045")
    full_name = models.CharField(max_length=150)
    profile_pic = models.ImageField(upload_to='students/profiles/', blank=True, null=True)
    department = models.CharField(max_length=100, help_text="e.g. Computer Science, Software Engineering")
    semester = models.CharField(max_length=20, choices=Semester.choices, default=Semester.SEM_1)
    phone_number = models.CharField(max_length=25, help_text="Student contact number")
    hostel_room_no = models.CharField(max_length=50, help_text="e.g. Ali Hall Room 101-A")
    email = models.EmailField(help_text="Official / Personal email")
    joining_date = models.DateField(default=timezone.now)
    mess_status = models.CharField(max_length=20, choices=MessStatus.choices, default=MessStatus.ACTIVE)
    monthly_mess_fee = models.DecimalField(max_digits=10, decimal_places=2, default=4500.00, help_text="Standard monthly mess subscription fee (PKR)")
    emergency_contact = models.CharField(max_length=100, help_text="Parent/Guardian contact number and relation")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_id']
        verbose_name = "Student Mess Profile"
        verbose_name_plural = "Student Mess Profiles"

    def __str__(self):
        return f"{self.student_id} - {self.full_name} ({self.hostel_room_no})"

    @property
    def total_outstanding_balance(self):
        """Sum of unpaid balances across all monthly mess fees."""
        unpaid_fees = self.mess_fees.filter(status__in=[MessFee.FeeStatus.UNPAID, MessFee.FeeStatus.PARTIAL, MessFee.FeeStatus.OVERDUE])
        return sum((fee.remaining_balance for fee in unpaid_fees), Decimal('0.00'))

    @property
    def initials(self):
        parts = self.full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        return "ST"


class MealMenu(models.Model):
    """
    Daily and Weekly Meal Menu for Breakfast, Lunch, Evening Tea, and Dinner.
    """
    class MealType(models.TextChoices):
        BREAKFAST = 'BREAKFAST', 'Breakfast'
        LUNCH = 'LUNCH', 'Lunch'
        EVENING_TEA = 'EVENING_TEA', 'Evening Tea'
        DINNER = 'DINNER', 'Dinner'

    class DayOfWeek(models.TextChoices):
        MONDAY = 'MONDAY', 'Monday'
        TUESDAY = 'TUESDAY', 'Tuesday'
        WEDNESDAY = 'WEDNESDAY', 'Wednesday'
        THURSDAY = 'THURSDAY', 'Thursday'
        FRIDAY = 'FRIDAY', 'Friday'
        SATURDAY = 'SATURDAY', 'Saturday'
        SUNDAY = 'SUNDAY', 'Sunday'

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        SERVING = 'SERVING', 'Serving Now'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    date = models.DateField(default=timezone.now)
    day_of_week = models.CharField(max_length=15, choices=DayOfWeek.choices)
    meal_type = models.CharField(max_length=20, choices=MealType.choices)
    menu_items = models.TextField(help_text="Items served (e.g. Paratha, Omelette, Tea)")
    serving_time = models.CharField(max_length=100, help_text="e.g. 7:30 AM - 9:00 AM")
    special_instructions = models.TextField(blank=True, help_text="e.g. Hot tea refill, sweet dish, salad bar")
    food_image = models.ImageField(upload_to='menu/dishes/', blank=True, null=True, help_text="Optional photo of the prepared meal")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'meal_type']
        constraints = [
            models.UniqueConstraint(fields=['date', 'meal_type'], name='unique_daily_meal_menu')
        ]
        verbose_name = "Daily Meal Menu"
        verbose_name_plural = "Daily Meal Menus"

    def save(self, *args, **kwargs):
        if self.date and not self.day_of_week:
            self.day_of_week = self.date.strftime('%A').upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} ({self.get_day_of_week_display()}) - {self.get_meal_type_display()}"


class MealAttendance(models.Model):
    """
    Meal Attendance Tracking for each meal with zero duplicate protection.
    """
    class AttendanceStatus(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='meal_attendances')
    date = models.DateField(default=timezone.now)
    meal_type = models.CharField(max_length=20, choices=MealMenu.MealType.choices)
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now=True)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-date', 'meal_type', 'student__student_id']
        constraints = [
            models.UniqueConstraint(fields=['student', 'date', 'meal_type'], name='unique_student_meal_attendance')
        ]
        verbose_name = "Meal Attendance"
        verbose_name_plural = "Meal Attendances"

    def __str__(self):
        return f"{self.student.student_id} - {self.date} ({self.get_meal_type_display()}): {self.status}"


class MessFee(models.Model):
    """
    Monthly Mess Fee records for students.
    """
    class FeeStatus(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PARTIAL = 'PARTIAL', 'Partially Paid'
        PAID = 'PAID', 'Fully Paid'
        OVERDUE = 'OVERDUE', 'Overdue'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mess_fees')
    billing_month = models.CharField(max_length=30, help_text="e.g. October 2026")
    month_date = models.DateField(help_text="1st of the billing month for sorting")
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4500.00'))
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=FeeStatus.choices, default=FeeStatus.UNPAID)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month_date', 'student__student_id']
        constraints = [
            models.UniqueConstraint(fields=['student', 'billing_month'], name='unique_student_monthly_mess_fee')
        ]
        verbose_name = "Mess Fee Invoice"
        verbose_name_plural = "Mess Fee Invoices"

    @property
    def remaining_balance(self):
        total = Decimal(str(self.total_fee)) if self.total_fee is not None else Decimal('0.00')
        paid = Decimal(str(self.amount_paid)) if self.amount_paid is not None else Decimal('0.00')
        balance = total - paid
        return max(balance, Decimal('0.00'))

    @property
    def is_overdue(self):
        return self.status in [self.FeeStatus.UNPAID, self.FeeStatus.PARTIAL, self.FeeStatus.OVERDUE] and self.due_date < timezone.now().date()

    def update_status(self):
        total = Decimal(str(self.total_fee)) if self.total_fee is not None else Decimal('0.00')
        paid = Decimal(str(self.amount_paid)) if self.amount_paid is not None else Decimal('0.00')
        if paid >= total and total > Decimal('0.00'):
            self.status = self.FeeStatus.PAID
        elif paid > Decimal('0.00'):
            self.status = self.FeeStatus.PARTIAL
        elif self.due_date and self.due_date < timezone.now().date():
            self.status = self.FeeStatus.OVERDUE
        else:
            self.status = self.FeeStatus.UNPAID
        self.save()

    def __str__(self):
        return f"{self.student.student_id} - {self.billing_month} (Rs. {self.total_fee}) [{self.get_status_display()}]"


class FeePayment(models.Model):
    """
    Individual Fee Payment Transaction recorded against a MessFee invoice.
    """
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash Counter'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer (HBL / NBP)'
        EASYPAISA = 'EASYPAISA', 'EasyPaisa'
        JAZZCASH = 'JAZZCASH', 'JazzCash'
        ONE_BILL = 'ONE_BILL', '1-Bill / 1-Link Online'

    mess_fee = models.ForeignKey(MessFee, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Bank Scroll / TRX Reference Number")
    receipt_slip = models.FileField(upload_to='payments/slips/', blank=True, null=True, help_text="Bank deposit slip / digital payment screenshot")
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = "Fee Payment"
        verbose_name_plural = "Fee Payments"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            # Recompute total amount paid on the related mess fee
            total_paid = self.mess_fee.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            self.mess_fee.amount_paid = Decimal(str(total_paid))
            self.mess_fee.update_status()

    def __str__(self):
        return f"Payment #{self.id} - {self.student.student_id} (Rs. {self.amount}) on {self.payment_date}"


class MessExpense(models.Model):
    """
    Daily and Monthly Mess Operating Expenses (Food, Groceries, LPG, Utilities, Maintenance).
    """
    class Category(models.TextChoices):
        FOOD = 'FOOD', 'Food Purchasing (Meat, Chicken, Veg, Dairy)'
        GROCERY = 'GROCERY', 'Grocery (Rice, Atta/Flour, Cooking Oil, Spices)'
        UTILITY = 'UTILITY', 'Gas & Utility (LPG Cylinder, Electric, Water)'
        OTHER = 'OTHER', 'Other / Maintenance (Cleaning, Utensils, Cook Helper)'

    category = models.CharField(max_length=30, choices=Category.choices, default=Category.FOOD)
    title = models.CharField(max_length=150, help_text="Short description of expense (e.g. 50kg Chicken purchasing)")
    expense_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, help_text="Vendor name, invoice number, quantity")
    bill_receipt = models.FileField(upload_to='expenses/bills/', blank=True, null=True, help_text="Scanned receipt or bill image")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = "Mess Expense"
        verbose_name_plural = "Mess Expenses"

    def __str__(self):
        return f"{self.expense_date} - {self.title} (Rs. {self.amount}) [{self.get_category_display()}]"


class Announcement(models.Model):
    """
    Mess Notice Board and Administrator Announcements.
    """
    class Category(models.TextChoices):
        MENU = 'MENU', 'Menu Change'
        TIMING = 'TIMING', 'Mess Timing Update'
        FEE = 'FEE', 'Fee Submission Deadline'
        SPECIAL_MEAL = 'SPECIAL_MEAL', 'Special Meal / Feast Notice'
        NOTICE = 'NOTICE', 'General Hostel Mess Notice'

    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        IMPORTANT = 'IMPORTANT', 'Important'
        URGENT = 'URGENT', 'Urgent Alert'

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.NOTICE)
    priority = models.CharField(max_length=15, choices=Priority.choices, default=Priority.NORMAL)
    content = models.TextField()
    published_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_date', '-created_at']
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} ({self.published_date})"
