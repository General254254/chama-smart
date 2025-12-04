from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# User Roles
ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('member', 'Member'),
    ('treasurer', 'Treasurer'),
    ('chairperson', 'Chairperson'),
]

# User Profile with role
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_treasurer(self):
        return self.role == 'treasurer'
    
    def is_chairperson(self):
        return self.role == 'chairperson'

# Chama Group
class Chama(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_chamas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    contribution_frequency = models.CharField(max_length=50, default='Monthly', help_text="e.g., Monthly, Weekly, Daily")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Chamas"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_total_contributions(self):
        return self.contributions.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    def get_member_count(self):
        return self.memberships.filter(is_active=True).count()
    
    def get_admin_members(self):
        return self.memberships.filter(role__in=['admin', 'chairperson'], is_active=True)

# Membership in Chama
class Membership(models.Model):
    MEMBER_ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('treasurer', 'Treasurer'),
        ('chairperson', 'Chairperson'),
    ]
    
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=MEMBER_ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['chama', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.chama.name} ({self.role})"
    
    def can_edit_chama(self):
        return self.role in ['admin', 'chairperson'] and self.is_active
    
    def can_add_transactions(self):
        return self.role in ['admin', 'treasurer', 'chairperson'] and self.is_active
    
    def get_total_contributions(self):
        return self.contributions.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    def get_pending_amount(self):
        # Calculate based on expected contributions vs actual
        if not self.chama.contribution_amount:
            return Decimal('0.00')
        # This is a simplified calculation - you might want to track expected contributions separately
        return Decimal('0.00')

# Contribution
class Contribution(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.membership.user.username} - {self.amount} on {self.date}"
    
    @property
    def chama(self):
        return self.membership.chama

# Transaction
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('contribution', 'Contribution'),
        ('withdrawal', 'Withdrawal'),
        ('loan', 'Loan'),
        ('expense', 'Expense'),
        ('dividend', 'Dividend'),
        ('other', 'Other'),
    ]
    
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date = models.DateField()
    purpose = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.chama.name} - {self.transaction_type} - {self.amount} on {self.date}"

# Announcement
class Announcement(models.Model):
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    is_important = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_important', '-created_at']
    
    def __str__(self):
        return f"{self.chama.name} - {self.title}"

# Private Message
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username} - {self.subject}"
