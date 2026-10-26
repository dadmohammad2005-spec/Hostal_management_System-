from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    StudentProfile, MealMenu, MealAttendance, MessFee, FeePayment, MessExpense, Announcement
)


class StudentProfileForm(forms.ModelForm):
    """
    Administrator form to Add / Edit Student Mess Profile with image upload validation.
    """
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        label="Auto-create student portal login account",
        help_text="Will create user with username as Student ID and default password 'student123'."
    )

    class Meta:
        model = StudentProfile
        fields = [
            'student_id', 'full_name', 'profile_pic', 'department', 'semester',
            'phone_number', 'hostel_room_no', 'email', 'joining_date',
            'mess_status', 'monthly_mess_fee', 'emergency_contact', 'is_active'
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. FA22-BCS-045'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Muhammad Ali Hassan'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92-300-1234567'}),
            'hostel_room_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ali Hall Room 101-A'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@iub.edu.pk'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'mess_status': forms.Select(attrs={'class': 'form-select'}),
            'monthly_mess_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father/Guardian Name & Phone'}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_profile_pic(self):
        pic = self.cleaned_data.get('profile_pic')
        if pic:
            # Validate file size (max 5MB)
            if pic.size > 5 * 1024 * 1024:
                raise ValidationError("Profile image size cannot exceed 5MB.")
            # Validate extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            if not any(pic.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError("Only JPG, JPEG, PNG, or WebP image formats are permitted.")
        return pic


class StudentSelfProfileForm(forms.ModelForm):
    """
    Student self-service form: only allowed to update contact, emergency contact, and photo.
    """
    class Meta:
        model = StudentProfile
        fields = ['phone_number', 'emergency_contact', 'profile_pic']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_profile_pic(self):
        pic = self.cleaned_data.get('profile_pic')
        if pic:
            if pic.size > 5 * 1024 * 1024:
                raise ValidationError("Image size cannot exceed 5MB.")
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            if not any(pic.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError("Only JPG, PNG, or WebP images are allowed.")
        return pic


class MealMenuForm(forms.ModelForm):
    """
    Form to Create / Update Daily & Weekly Meal Menus.
    """
    class Meta:
        model = MealMenu
        fields = [
            'date', 'meal_type', 'menu_items', 'serving_time',
            'special_instructions', 'food_image', 'status'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'menu_items': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'e.g. Paratha, Omelette, Karak Chai (separate with commas)'}),
            'serving_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 7:30 AM - 9:00 AM'}),
            'special_instructions': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'e.g. Extra sweet dish for post-Jumma prayer'}),
            'food_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class BulkMessFeeGenerateForm(forms.Form):
    """
    Form to bulk generate monthly mess bills for all active residents.
    """
    billing_month = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. November 2026'})
    )
    month_date = forms.DateField(
        initial=timezone.now,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    total_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=4500.00,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Cycle billing remarks'})
    )


class FeePaymentForm(forms.ModelForm):
    """
    Form to record fee payments.
    """
    class Meta:
        model = FeePayment
        fields = ['mess_fee', 'amount', 'payment_date', 'payment_method', 'transaction_id', 'receipt_slip', 'notes']
        widgets = {
            'mess_fee': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. HBL-992244 or Cash Receipt #'}),
            'receipt_slip': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Additional cashier notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to unpaid or partially paid fees
        self.fields['mess_fee'].queryset = MessFee.objects.filter(
            status__in=[MessFee.FeeStatus.UNPAID, MessFee.FeeStatus.PARTIAL, MessFee.FeeStatus.OVERDUE]
        ).select_related('student')


class MessExpenseForm(forms.ModelForm):
    """
    Form to record mess expenses (Groceries, Meat/Veg, Utilities, LPG, Kitchen Staff).
    """
    class Meta:
        model = MessExpense
        fields = ['category', 'title', 'expense_date', 'amount', 'description', 'bill_receipt']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50kg Chicken Purchasing'}),
            'expense_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Vendor details, item breakdown, quantities'}),
            'bill_receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class AnnouncementForm(forms.ModelForm):
    """
    Form to publish administrator notices and announcements.
    """
    class Meta:
        model = Announcement
        fields = ['title', 'category', 'priority', 'content', 'published_date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement Heading'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Detailed announcement content...'}),
            'published_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
