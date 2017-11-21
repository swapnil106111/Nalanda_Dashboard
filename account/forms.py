from django import forms
from django.contrib.auth.models import User, Group
import re
from django.core.exceptions import ObjectDoesNotExist
from account.models import UserInfoSchool, UserRoleCollectionMapping, UserInfoClass
from django.contrib.auth.forms import PasswordResetForm

# class Forget_Password(forms.ModelForm):
#     email = forms.EmailField(required=False)
#     class Meta:
#         model = User
#         fields = ['email']

class EmailValidationOnForgotPassword(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("There is no user registered with the specified email address!")

        return email

class UserProfileForm(forms.ModelForm):
    role = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   required=True)
    institutes = forms.ModelChoiceField(queryset=UserInfoSchool.objects.all(),
    	                           required=False, label = 'Institutes')
    classes = forms.CharField(label='Classes', required = False)
    password=forms.CharField(label='Password', widget=forms.PasswordInput())
    confirm_password=forms.CharField(label = 'Confirm Password', widget=forms.PasswordInput())
    email = forms.CharField(max_length=75, required=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password','role', 'institutes', 'classes']

    def clean(self):
        cleaned_data = super(UserProfileForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "password and confirm_password does not match"
            )


    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError('Username can only contain \
            	alphanumeric characters and the underscore.')
        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username
        raise forms.ValidationError('Username is already taken.')

    def save(self, commit=True):
        # instance = super(SelectCourseYear, self).save(commit=False)
        user = User.objects.create_user(self.cleaned_data['username'])
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['confirm_password'])
        user.is_active = False
        if commit:
            user.save() 
            user.groups.clear()
            user.groups.add(self.cleaned_data['role'])
        return user



