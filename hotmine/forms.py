from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile
import re


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "name@example.com"}
        ),
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First Name"}
        ),
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last Name"}
        ),
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+1 801 234 5678"}
        ),
        help_text="Enter a valid phone number with country code",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm password"}
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")

        # Remove all spaces and hyphens for validation
        clean_phone = re.sub(r"[\s\-]", "", phone_number)

        # Pattern for international format (+XXX followed by 10-14 digits)
        international_pattern = r"^\+\d{1,3}\d{9,13}$"

        # Pattern for local format (starts with 0 and has 10-11 digits total)
        local_pattern = r"^0\d{9,10}$"

        # Pattern for simple digit format (10-15 digits)
        simple_pattern = r"^\d{10,15}$"

        if not (
            re.match(international_pattern, clean_phone)
            or re.match(local_pattern, clean_phone)
            or re.match(simple_pattern, clean_phone)
        ):
            raise ValidationError(
                "Enter a valid phone number. Examples: +1 801 234 5678, 08012345678, or 2348012345678"
            )

        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username or Email"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter password"}
        )
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Allow login with email
        if "@" in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username


class UserUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""

    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First Name"}
        ),
    )
    last_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last Name"}
        ),
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+1 801 234 5678"}
        ),
        help_text="Enter a valid phone number with country code",
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "name@example.com"}
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args, **kwargs):
        # Extract the user instance if provided
        self.user = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        # Update widget attributes
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Username"}
        )

        # If user has a profile, populate phone_number
        if self.user and hasattr(self.user, "userprofile"):
            self.fields["phone_number"].initial = self.user.userprofile.phone_number

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Check if email is taken by another user (excluding current user)
        if self.user:
            existing_user = User.objects.filter(email=email).exclude(pk=self.user.pk)
            if existing_user.exists():
                raise ValidationError("A user with this email already exists.")
        else:
            if User.objects.filter(email=email).exists():
                raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Check if username is taken by another user (excluding current user)
        if self.user:
            existing_user = User.objects.filter(username=username).exclude(
                pk=self.user.pk
            )
            if existing_user.exists():
                raise ValidationError("A user with this username already exists.")
        else:
            if User.objects.filter(username=username).exists():
                raise ValidationError("A user with this username already exists.")
        return username

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")

        # If phone number is empty, return it (since it's not required)
        if not phone_number:
            return phone_number

        # Remove all spaces and hyphens for validation
        clean_phone = re.sub(r"[\s\-]", "", phone_number)

        # Pattern for international format (+XXX followed by 10-14 digits)
        international_pattern = r"^\+\d{1,3}\d{9,13}$"

        # Pattern for local format (starts with 0 and has 10-11 digits total)
        local_pattern = r"^0\d{9,10}$"

        # Pattern for simple digit format (10-15 digits)
        simple_pattern = r"^\d{10,15}$"

        if not (
            re.match(international_pattern, clean_phone)
            or re.match(local_pattern, clean_phone)
            or re.match(simple_pattern, clean_phone)
        ):
            raise ValidationError(
                "Enter a valid phone number. Examples: +1 801 234 5678, 08012345678, or 2348012345678"
            )

        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)

        # Explicitly set the email field to ensure it's updated
        user.email = self.cleaned_data.get("email")

        if commit:
            user.save()

            # Handle UserProfile update/creation
            phone_number = self.cleaned_data.get("phone_number", "")
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = phone_number
            profile.save()

        return user


class PasswordUpdateForm(forms.Form):
    """Separate form for password updates"""

    current_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Current Password"}
        ),
        help_text="Enter your current password",
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "New Password"}
        ),
        help_text="Your password must contain at least 8 characters.",
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm New Password"}
        ),
        help_text="Enter the same password as before, for verification.",
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise ValidationError("Your current password is incorrect.")
        return current_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")

        if password1 and password2:
            if password1 != password2:
                raise ValidationError("The two password fields didn't match.")
        return password2

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")

        # Basic password validation
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        # You can add more password validation rules here
        # For example, checking for numbers, special characters, etc.

        return password

    def save(self, commit=True):
        password = self.cleaned_data.get("new_password1")
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
