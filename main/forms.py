from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from main.models import Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)


class VkAuthForm(forms.Form):
    login = forms.CharField(label=_('Phone or email'), required=True)
    password = forms.CharField(label=_('Password'), required=True, widget=forms.PasswordInput)


class RecoverForm(forms.Form):
    username = forms.CharField(label='User')


class UserProfileForm(ModelForm):
    img = forms.ImageField(label='Avatar', required=False)

    class Meta:
        model = Profile
        fields = ('has_vk', 'has_tm', 'use_bot',)


class TMMessageForm(forms.Form):
    id = forms.CharField(label='Id')
    text = forms.CharField(label=_('Message'))


class TMPhoneForm(forms.Form):
    phone = forms.CharField(label=_('Your phone'))


class TMCodeForm(forms.Form):
    code = forms.CharField(label=_('Your code'))
