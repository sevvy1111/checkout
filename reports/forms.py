# reports/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import UserReport

User = get_user_model()

class UserReportForm(forms.ModelForm):
    reported_username = forms.CharField(label="Username of the user you are reporting", max_length=150)

    class Meta:
        model = UserReport
        fields = ['reported_username', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_reported_username(self):
        """
        Validate that the user being reported actually exists.
        """
        username = self.cleaned_data.get('reported_username')
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("A user with this username does not exist.")
        return username