# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Profile
from listings.models import Order
User = get_user_model()


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'phone']

    def clean_phone(self):

        phone_number = self.cleaned_data.get('phone')
        if not phone_number:
            return phone_number

        phone_number = ''.join(filter(str.isdigit, phone_number))

        if phone_number.startswith('09') and len(phone_number) == 11:
            return phone_number[1:]

        if phone_number.startswith('9') and len(phone_number) == 10:
            return phone_number

        raise forms.ValidationError(
            "Invalid phone number format. Please use '09xxxxxxxxx' or '9xxxxxxxxx'."
        )

    class OrderStatusForm(forms.ModelForm):
        class Meta:
            model = Order
            fields = ['status']
            widgets = {
                'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            }