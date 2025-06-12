from django import forms
from .models import UserMaster

class UserMasterForm(forms.ModelForm):
    class Meta:
        model = UserMaster
        fields = '__all__'
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }
