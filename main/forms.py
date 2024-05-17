from django import forms
from .models import MyUser,StudentGroup
from django.contrib.auth.password_validation import validate_password

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    surname = forms.CharField(max_length=30)
    course = forms.IntegerField()
    group = forms.CharField(max_length=30, required=True,error_messages={'required': 'Введите название группы.'})
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean_password(self):
        password = self.cleaned_data['password']
        if validate_password(password) is not None:
            raise forms.ValidationError("Пароль должен содержать хотя бы одну цифру, одну букву в верхнем и нижнем регистрах, а также один специальный символ.")
        return password

    def clean_email(self):
        email = self.cleaned_data['email']
        if validate_email(email) is not None:
            raise forms.ValidationError("Некорректный адрес электронной почты.")
        if MyUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким адресом электронной почты уже существует.")
        return email
    def clean_group(self):
        group_name = self.cleaned_data.get('group')
        if not StudentGroup.objects.filter(name=group_name).exists():
            raise forms.ValidationError("Группа с таким названием не существует.")
        return group_name