from django.db import models
from django.db import models
from django.contrib.auth.models import User

# Chama Group
class ChamaGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # links to Django user
    group = models.ForeignKey(ChamaGroup, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.user.username


class Contribution(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.member.user.username} - {self.amount}"
