from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import User


class RollNumberOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that supports:
    1. Student University Roll Number (registration_no, e.g. FA22-BCS-001, fa22-bcs-001)
    2. Username (case-insensitive, e.g. admin, chief_warden, warden_ali_hall, student_ali)
    3. Student CNIC number (raw 13-digits e.g. 5440166878999 or formatted e.g. 54401-6687899-9)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        identifier = username.strip()
        # Clean digits for CNIC matching
        identifier_digits = "".join(ch for ch in identifier if ch.isdigit())

        # Construct query
        q_filter = Q(username__iexact=identifier) | Q(registration_no__iexact=identifier)

        if identifier_digits and len(identifier_digits) >= 10:
            q_filter |= Q(cnic__iexact=identifier)
            q_filter |= Q(cnic__iexact=identifier_digits)
            q_filter |= Q(cnic_or_id__iexact=identifier)
            q_filter |= Q(cnic_or_id__icontains=identifier_digits)
        else:
            q_filter |= Q(cnic_or_id__iexact=identifier)

        user = User.objects.filter(q_filter).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
