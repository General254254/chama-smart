from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (
    UserProfile, Chama, Membership, Contribution, 
    Transaction, Announcement, Message
)
from decimal import Decimal

class MemberRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(
        choices=[('member', 'Member')], 
        initial='member',
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                role='member',
                phone_number=self.cleaned_data.get('phone_number', '')
            )
        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'date_of_birth', 'role']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.email = self.cleaned_data['email']
            profile.user.save()
            profile.save()
        return profile

class ChamaForm(forms.ModelForm):
    class Meta:
        model = Chama
        fields = ['name', 'description', 'contribution_amount', 'contribution_frequency']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'contribution_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
        labels = {
            'contribution_amount': 'Contribution Amount',
            'contribution_frequency': 'Contribution Frequency',
        }

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['amount', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'date', 'purpose', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_important']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'content', 'chama']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
            'chama': forms.Select(attrs={'required': False}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Only show chamas the user is a member of
            user_chamas = Chama.objects.filter(memberships__user=user, memberships__is_active=True).distinct()
            self.fields['chama'].queryset = user_chamas
            # Only show other members as recipients
            recipient_ids = Membership.objects.filter(
                chama__in=user_chamas,
                is_active=True
            ).exclude(user=user).values_list('user_id', flat=True).distinct()
            self.fields['recipient'].queryset = User.objects.filter(id__in=recipient_ids)

class JoinChamaForm(forms.Form):
    chama_id = forms.IntegerField(widget=forms.HiddenInput())
