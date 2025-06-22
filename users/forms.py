from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Staff ID",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 text-white border border-gray-600 rounded-lg py-3 px-4 pl-12 focus:outline-none focus:border-purple-500',
            'placeholder': 'e.g., 123456',
            'pattern': '\\d{1,6}',
            'title': 'Staff ID must be up to 6 digits.'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-gray-700 text-white border border-gray-600 rounded-lg py-3 px-4 pl-12 focus:outline-none focus:border-purple-500',
            'placeholder': '••••••••'
        })
    )

