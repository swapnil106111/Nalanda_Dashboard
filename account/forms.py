from django import forms
from django.contrib.auth.models import User, Group
import re
from django.core.exceptions import ObjectDoesNotExist
from account.models import UserInfoSchool, UserRoleCollectionMapping, UserInfoClass

class UserProfileForm(forms.ModelForm):
    role = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   required=True)
    institutes = forms.ModelChoiceField(queryset=UserInfoSchool.objects.all(),
    	                           required=False, label = 'Institutes')
    classes = forms.CharField(label='Classes', required = False)
    password1 = forms.CharField(label='Password',
                          widget=forms.PasswordInput())
    password2 = forms.CharField(label='Confirm Password',
                        widget=forms.PasswordInput())
    email = forms.CharField(max_length=75, required=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1','password2','role', 'institutes', 'classes']

    def clean_password(self):
        if 'password1' in self.cleaned_data:
            password1 = self.cleaned_data['password1']
            password2 = self.cleaned_data['password2']
            if password1 == password2:
                return password2
        raise forms.ValidationError('Passwords do not match.')

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
        print ("Data:", self.cleaned_data)
        # instance = super(SelectCourseYear, self).save(commit=False)
        user = User.objects.create_user(self.cleaned_data['username'])
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['password2'])
        user.is_active = False
        if commit:
            user.save() 
            user.groups.clear()
            user.groups.add(self.cleaned_data['role'])
        return user



