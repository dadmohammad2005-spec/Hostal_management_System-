import os
from django import forms
from django.db.models import Q
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    User, Hostel, Block, Room, Bed, Allotment,
    FeeVoucher, Complaint, GatePass, MessSchedule,
    RoomChangeRequest, Notification, HostelAnnouncement
)


def validate_voucher_file(file):
    """Validate uploaded fee voucher format (PDF, JPG, PNG) and file size."""
    if not file:
        raise ValidationError("Please attach a valid fee voucher document or payment receipt.")
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f"Invalid file format '{ext}'. Uploads must be in PDF, JPG, or PNG format.")
    # 10MB limit
    if file.size > 10 * 1024 * 1024:
        raise ValidationError("File size exceeds 10MB. Please upload a smaller receipt image or PDF.")
    return file


class StudentCNICSearchForm(forms.Form):
    """Admin search form for students by CNIC."""
    cnic = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-11 pr-4 py-3 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:bg-white transition-all outline-none',
            'placeholder': 'Enter 13-digit Student CNIC (e.g. 5440166878999 or 54401-6687899-9)',
            'autocomplete': 'off',
            'id': 'cnic_search_input'
        })
    )


class LoginForm(AuthenticationForm):
    """
    Common Login Form for all roles (Students, Wardens, Chief Wardens, Administrators).
    Accepts Roll Number or assigned User ID and Password.
    """
    username = forms.CharField(
        label="Roll Number or User ID",
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-11 pr-4 py-3 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:bg-white transition-all outline-none',
            'placeholder': 'Enter your Roll Number or User ID',
            'id': 'id_username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full pl-11 pr-11 py-3 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:bg-white transition-all outline-none',
            'placeholder': 'Enter your password',
            'id': 'id_password',
            'autocomplete': 'current-password',
        })
    )


class StudentRegistrationForm(forms.ModelForm):
    """Student Registration Form with academic data and document attachments."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none',
            'placeholder': 'Create a secure password'
        }),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none',
            'placeholder': 'Repeat your password'
        })
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'registration_no', 'department', 'semester', 'cnic', 'cnic_or_id',
            'gender', 'emergency_contact', 'address', 'profile_pic',
            'document_cnic', 'document_admission_slip'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. ali_khan or fa22-bcs-045'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'student@iub.edu.pk'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': '+92-300-1234567'}),
            'registration_no': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. FA22-BCS-045'}),
            'department': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. Computer Science, Software Eng'}),
            'semester': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. 1st, 3rd, 5th'}),
            'cnic': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': '13-digit CNIC (e.g. 5440166878999)'}),
            'cnic_or_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'CNIC / Form-B'}),
            'gender': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Father/Guardian contact'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Permanent Home Address'}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100', 'id': 'id_profile_pic'}),
            'document_cnic': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700'}),
            'document_admission_slip': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700'}),
        }

    def clean_registration_no(self):
        reg_no = self.cleaned_data.get('registration_no', '').strip()
        if reg_no:
            qs = User.objects.filter(registration_no__iexact=reg_no)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f"A student account with Roll Number '{reg_no}' already exists.")
        return reg_no

    def clean_cnic_or_id(self):
        cnic_val = self.cleaned_data.get('cnic_or_id', '').strip()
        if cnic_val:
            digits = "".join(ch for ch in cnic_val if ch.isdigit())
            q = Q(cnic_or_id__iexact=cnic_val) | Q(cnic__iexact=cnic_val)
            if digits and len(digits) >= 10:
                q |= Q(cnic__iexact=digits) | Q(cnic_or_id__icontains=digits)
            qs = User.objects.filter(q)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f"A user with CNIC / ID '{cnic_val}' is already registered.")
        return cnic_val

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f"An account with email '{email}' is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        user.application_status = User.ApplicationStatus.PENDING
        user.set_password(self.cleaned_data['password'])
        if not user.cnic and user.cnic_or_id:
            user.cnic = user.cnic_or_id
        if commit:
            user.save()
        return user


class StudentProfileUpdateForm(forms.ModelForm):
    """Student Self-Profile Update Form with photo preview support."""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'cnic', 'phone_number', 'emergency_contact',
            'address', 'profile_pic', 'document_cnic', 'document_admission_slip', 'document_other'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'cnic': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': '13-digit CNIC'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100', 'id': 'profile_pic_input'}),
            'document_cnic': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700'}),
            'document_admission_slip': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700'}),
            'document_other': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700'}),
        }


class StudentApplicationReviewForm(forms.ModelForm):
    """Admin / Warden Form to approve or reject student hostel application."""
    class Meta:
        model = User
        fields = ['application_status', 'application_notes']
        widgets = {
            'application_status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'application_notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Reason for approval/rejection or instructions for student'}),
        }


class StaffUserForm(forms.ModelForm):
    """Admin creation & edit form for Wardens."""
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none',
            'placeholder': 'Set or change password'
        }),
        min_length=6
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'role', 'cnic_or_id', 'warden_designation', 'assigned_block',
            'can_manage_allocations', 'can_manage_complaints',
            'can_manage_gatepasses', 'can_manage_room_changes',
            'profile_pic'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'role': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'cnic_or_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'warden_designation': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'placeholder': 'e.g. Warden Ali Hall (Quaid Block)'}),
            'assigned_block': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.role or user.role == User.Role.STUDENT:
            user.role = User.Role.WARDEN
        user.is_staff = True
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user


class AllotmentForm(forms.ModelForm):
    """
    Room & Bed Allotment form with Zero Double-Booking validation and 2-student capacity limit.
    """
    class Meta:
        model = Allotment
        fields = ['student', 'room', 'bed', 'allotment_date', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'room': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'id': 'id_room'}),
            'bed': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'id': 'id_bed'}),
            'allotment_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Optional allotment notes or terms'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit student choices to active students who don't already have an active allotment
        active_student_ids = Allotment.objects.filter(is_active=True).values_list('student_id', flat=True)
        if self.instance and self.instance.pk:
            active_student_ids = [sid for sid in active_student_ids if sid != self.instance.student_id]
        
        self.fields['student'].queryset = User.objects.filter(
            role=User.Role.STUDENT,
            application_status__in=[User.ApplicationStatus.APPROVED, User.ApplicationStatus.PENDING, User.ApplicationStatus.ALLOCATED]
        ).exclude(id__in=active_student_ids)

        # Default bed choices to available beds plus the current bed if editing
        if self.instance and self.instance.pk:
            self.fields['bed'].queryset = Bed.objects.filter(
                models.Q(status=Bed.Status.AVAILABLE) | models.Q(pk=self.instance.bed_id)
            ).select_related('room', 'room__block')
        else:
            self.fields['bed'].queryset = Bed.objects.filter(status=Bed.Status.AVAILABLE).select_related('room', 'room__block')

    def clean(self):
        cleaned_data = super().clean()
        bed = cleaned_data.get('bed')
        room = cleaned_data.get('room')
        student = cleaned_data.get('student')

        if bed and room and bed.room_id != room.id:
            self.add_error('bed', f"Bed {bed.bed_code} does not belong to Room {room.room_number}.")

        if bed and bed.status != Bed.Status.AVAILABLE:
            if not (self.instance and self.instance.pk and self.instance.bed_id == bed.id):
                self.add_error('bed', f"Bed {bed.bed_code} is not available (Status: {bed.get_status_display()}).")

        if student:
            existing = Allotment.objects.filter(student=student, is_active=True)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                self.add_error('student', f"Student {student.username} already holds an active allotment in Room {existing.first().room.room_number}.")

        if room:
            current_count = Allotment.objects.filter(room=room, is_active=True)
            if self.instance and self.instance.pk:
                current_count = current_count.exclude(pk=self.instance.pk)
            if current_count.count() >= room.capacity:
                self.add_error('room', f"Room {room.room_number} is already at full capacity ({room.capacity} students).")

        return cleaned_data


class VacateForm(forms.Form):
    """Form to process bed checkout/vacation."""
    vacate_date = forms.DateField(
        initial=timezone.now,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Reason for vacating, key return status, room inspection notes'})
    )


class FeeVoucherCreateForm(forms.ModelForm):
    """Admin / Warden single voucher generation."""
    class Meta:
        model = FeeVoucher
        fields = ['student', 'fee_type', 'billing_month', 'amount', 'due_date', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'fee_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'billing_month': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. October 2026'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_student_ids = Allotment.objects.filter(is_active=True).values_list('student_id', flat=True)
        self.fields['student'].queryset = User.objects.filter(id__in=active_student_ids)


class BulkFeeGenerateForm(forms.Form):
    """Form to generate fee vouchers for all actively allotted students in one click."""
    fee_type = forms.ChoiceField(
        choices=FeeVoucher.FeeType.choices,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'})
    )
    billing_month = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. October 2026'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': '5000.00'})
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Notes on this bulk invoice cycle'})
    )


class FeePaymentProofForm(forms.ModelForm):
    """Student payment proof submission form with format validation."""
    class Meta:
        model = FeeVoucher
        fields = ['payment_method', 'transaction_id', 'payment_proof', 'payment_date']
        widgets = {
            'payment_method': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. HBL Konnect, EasyPaisa, JazzCash, NBP / HBL Branch Deposit'}),
            'transaction_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. TRX-9876543210 or Scroll No.'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'payment_proof': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100', 'accept': '.pdf,.jpg,.jpeg,.png', 'required': 'required'}),
        }

    def clean_payment_proof(self):
        proof = self.cleaned_data.get('payment_proof')
        return validate_voucher_file(proof)


class StudentFeeVoucherUploadForm(forms.ModelForm):
    """
    Dedicated form for students to upload new fee vouchers through their Student Portal.
    Allows uploading in PDF, JPG, or PNG format.
    """
    class Meta:
        model = FeeVoucher
        fields = [
            'fee_type', 'billing_month', 'amount',
            'payment_method', 'transaction_id', 'payment_date', 'payment_proof', 'remarks'
        ]
        widgets = {
            'fee_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'billing_month': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. October 2026 or Fall Semester 2026'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'step': '0.01', 'placeholder': '5000.00'}),
            'payment_method': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. HBL Konnect, EasyPaisa, JazzCash, 1-Bill, Bank Challan'}),
            'transaction_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. TRX-9876543210 or Bank Scroll / Receipt No.'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'payment_proof': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100', 'accept': '.pdf,.jpg,.jpeg,.png', 'required': 'required'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Optional remarks or deposit branch details'}),
        }

    def clean_payment_proof(self):
        proof = self.cleaned_data.get('payment_proof')
        return validate_voucher_file(proof)


class FeeVerificationForm(forms.ModelForm):
    """Staff fee verification form with support for Paid, Pending, Rejected."""
    class Meta:
        model = FeeVoucher
        fields = ['status', 'remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Verification notes, bank clearance confirmation, or reason for rejection...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit choices to manageable verification statuses: Paid, Pending, Rejected, Unpaid
        self.fields['status'].choices = [
            (FeeVoucher.Status.PAID, 'Paid (Approved & Verified)'),
            (FeeVoucher.Status.PENDING_VERIFICATION, 'Pending Verification'),
            (FeeVoucher.Status.REJECTED, 'Rejected (Declined with Remarks)'),
            (FeeVoucher.Status.UNPAID, 'Unpaid'),
        ]

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        remarks = cleaned_data.get('remarks')
        if status == FeeVoucher.Status.REJECTED and not remarks:
            self.add_error('remarks', "Please provide a reason or remarks explaining why the fee voucher is being rejected.")
        return cleaned_data


class ComplaintForm(forms.ModelForm):
    """Student Complaint Submission Form covering all 11 required categories."""
    class Meta:
        model = Complaint
        fields = ['title', 'category', 'room_number', 'priority', 'description', 'photo', 'supporting_attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Brief summary of the issue'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'room_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. Room 101'}),
            'priority': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Detailed description of the issue...'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100'}),
            'supporting_attachment': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700'}),
        }


class ComplaintUpdateForm(forms.ModelForm):
    """Admin / Warden Complaint Resolution, Assignment & Status Update Form."""
    class Meta:
        model = Complaint
        fields = ['status', 'priority', 'assigned_to', 'warden_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'priority': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'assigned_to': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'warden_remarks': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Staff resolution notes, technician remarks, or reason for rejection'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.WARDEN])


class RoomChangeRequestForm(forms.ModelForm):
    """Student Room-Change Request Submission Form."""
    class Meta:
        model = RoomChangeRequest
        fields = ['reason_category', 'detailed_explanation', 'preferred_room', 'supporting_document']
        widgets = {
            'reason_category': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'detailed_explanation': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Explain the exact difficulties or circumstances requiring a room change...'}),
            'preferred_room': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'supporting_document': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100'}),
        }

    def __init__(self, *args, **kwargs):
        student_user = kwargs.pop('student_user', None)
        super().__init__(*args, **kwargs)
        if student_user and student_user.active_allotment:
            # Exclude current room from preferred choices
            self.fields['preferred_room'].queryset = Room.objects.exclude(
                id=student_user.active_allotment.room_id
            ).filter(maintenance_status=Room.MaintenanceStatus.OPERATIONAL).select_related('block')


class RoomChangeWardenReviewForm(forms.ModelForm):
    """Warden Review & Field Recommendation Form for Room Changes."""
    class Meta:
        model = RoomChangeRequest
        fields = ['warden_recommendation', 'warden_remarks']
        widgets = {
            'warden_recommendation': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'warden_remarks': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'placeholder': 'Warden assessment notes, roommate interview findings, and recommendation'}),
        }


class RoomChangeAdminProcessForm(forms.ModelForm):
    """Admin Final Approval / Rejection and Target Bed Allocation Form."""
    class Meta:
        model = RoomChangeRequest
        fields = ['status', 'admin_remarks', 'new_room', 'new_bed']
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'admin_remarks': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'placeholder': 'Administrator approval/rejection remarks'}),
            'new_room': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'id': 'id_new_room'}),
            'new_bed': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'id': 'id_new_bed'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit choices to available beds
        self.fields['new_bed'].queryset = Bed.objects.filter(status=Bed.Status.AVAILABLE).select_related('room', 'room__block')


class HostelAnnouncementForm(forms.ModelForm):
    """Hostel Notice / Announcement Creation Form."""
    class Meta:
        model = HostelAnnouncement
        fields = ['title', 'category', 'priority', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Announcement title'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'priority': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Notice content...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-emerald-600 rounded focus:ring-emerald-500'}),
        }


class RoomMaintenanceForm(forms.ModelForm):
    """Room Maintenance Status Form."""
    class Meta:
        model = Room
        fields = ['maintenance_status']
        widgets = {
            'maintenance_status': forms.Select(attrs={'class': 'w-full px-4 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
        }


class GatePassRequestForm(forms.ModelForm):
    """Student Gate Pass / Leave Request Form."""
    class Meta:
        model = GatePass
        fields = ['reason', 'destination', 'emergency_contact', 'leave_date', 'return_date']
        widgets = {
            'reason': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. Weekend Home Visit, Family Event, Medical'}),
            'destination': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'City, Address, or Destination'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Emergency phone number'}),
            'leave_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'return_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        leave_date = cleaned_data.get('leave_date')
        return_date = cleaned_data.get('return_date')
        if leave_date and return_date and return_date <= leave_date:
            self.add_error('return_date', "Return date and time must be after the leave date.")
        return cleaned_data


class GatePassReviewForm(forms.ModelForm):
    """Warden Gate Pass Approval/Rejection Form."""
    class Meta:
        model = GatePass
        fields = ['status', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'rejection_reason': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Provide reason if rejected'}),
        }


class MessScheduleForm(forms.ModelForm):
    """Mess Menu Item Form."""
    class Meta:
        model = MessSchedule
        fields = ['day_of_week', 'meal_type', 'timing', 'menu_description', 'special_note']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'meal_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'timing': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. 7:30 AM - 9:30 AM'}),
            'menu_description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'Menu items'}),
            'special_note': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. Special Sweet Dish / Veg Option'}),
        }


class HostelForm(forms.ModelForm):
    class Meta:
        model = Hostel
        fields = ['name', 'gender_category', 'total_floors', 'contact_number', 'address', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'gender_category': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'total_floors': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'contact_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['block', 'room_number', 'floor', 'room_type', 'capacity', 'price_per_bed', 'maintenance_status']
        widgets = {
            'block': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'room_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'placeholder': 'e.g. 101'}),
            'floor': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'room_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'capacity': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
            'price_per_bed': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none', 'step': '0.01'}),
            'maintenance_status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none'}),
        }
