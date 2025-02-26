from django import forms
# from django.contrib.auth.forms import UserCreationForm
from .models import Account, ROLE, Location

class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=60, 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    full_name = forms.CharField(
        max_length=60, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    ssn = forms.CharField(
        max_length=9, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    user_role = forms.ChoiceField(
        choices=[(ROLE.MANAGER, ROLE.MANAGER.label), (ROLE.TOUROP, ROLE.TOUROP.label)], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Account
        fields = ("email", "full_name", "ssn", "user_role")
    
    def save(self, commit=True):
        user = Account.objects.create_user(
            email=self.cleaned_data['email'],
            full_name=self.cleaned_data['full_name'],
            ssn=self.cleaned_data['ssn'],
            password=Account.objects.make_random_password(),
            user_role=self.cleaned_data['user_role']
        )
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username', 
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
class EditLocationForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control form-control-lg autoresize'}))

    class Meta:
        model = Location
        fields = ['name', 'address']

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label='Email', 
        max_length=60, 
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    ssn = forms.CharField(
        label='SSN',
        max_length=11, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )