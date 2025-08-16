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
