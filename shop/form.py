from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Address, Review, ContactMessage

INPUT_CLASS = 'w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-100 outline-none transition'


class CustomUserForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Choose a username'}))
    email = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@example.com'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Create a password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class AddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'address_line', 'city', 'state', 'pincode', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Full name'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '10-digit mobile number'}),
            'address_line': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'House no., street, area'}),
            'city': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Pincode'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)], attrs={'class': INPUT_CLASS}),
            'title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Review title'}),
            'comment': forms.Textarea(attrs={'class': INPUT_CLASS, 'placeholder': 'Share your experience with this product', 'rows': 4}),
        }


class PasswordChangeCustomForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Enter your current password'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Enter new password (min 6 chars)'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Confirm new password'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Current password is incorrect.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_pwd = cleaned_data.get('new_password')
        confirm_pwd = cleaned_data.get('confirm_password')
        if new_pwd and confirm_pwd:
            if new_pwd != confirm_pwd:
                raise forms.ValidationError("New passwords do not match.")
            if len(new_pwd) < 6:
                raise forms.ValidationError("New password must be at least 6 characters long.")
        return cleaned_data


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@example.com'}),
            'subject': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'What can we help you with?'}),
            'message': forms.Textarea(attrs={'class': INPUT_CLASS, 'placeholder': 'Write your question or feedback in detail...', 'rows': 5}),
        }
