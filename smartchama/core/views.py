from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    UserProfile, Chama, Membership, Contribution, 
    Transaction, Announcement, Message
)
from .forms import (
    MemberRegistrationForm, UserProfileForm, ChamaForm, 
    ContributionForm, TransactionForm, AnnouncementForm, 
    MessageForm, JoinChamaForm
)

# Authentication Views
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Smart Chama.')
            return redirect('dashboard')
    else:
        form = MemberRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('user_login')

# Profile Views
@login_required
def profile(request):
    profile_obj, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile_obj)
    return render(request, 'core/profile.html', {'form': form, 'profile': profile_obj})

# Dashboard Views
@login_required
def dashboard(request):
    profile_obj, created = UserProfile.objects.get_or_create(user=request.user)
    user_chamas = Chama.objects.filter(memberships__user=request.user, memberships__is_active=True).distinct()
    
    # User's contributions summary
    user_contributions = Contribution.objects.filter(membership__user=request.user)
    total_contributions = user_contributions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Recent contributions
    recent_contributions = user_contributions.order_by('-date')[:5]
    
    # Recent announcements
    recent_announcements = Announcement.objects.filter(
        chama__in=user_chamas
    ).order_by('-created_at')[:5]
    
    # Unread messages
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'profile': profile_obj,
        'user_chamas': user_chamas,
        'total_contributions': total_contributions,
        'recent_contributions': recent_contributions,
        'recent_announcements': recent_announcements,
        'unread_messages': unread_messages,
    }
    
    # Admin dashboard stats
    if profile_obj.is_admin():
        all_chamas = Chama.objects.all()
        all_members = User.objects.filter(memberships__is_active=True).distinct().count()
        total_chama_contributions = Contribution.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context.update({
            'all_chamas': all_chamas,
            'all_members': all_members,
            'total_chama_contributions': total_chama_contributions,
        })
    
    return render(request, 'core/dashboard.html', context)

# Chama Views
@login_required
def chama_list(request):
    user_chamas = Chama.objects.filter(memberships__user=request.user, memberships__is_active=True).distinct()
    available_chamas = Chama.objects.filter(is_active=True).exclude(
        memberships__user=request.user, 
        memberships__is_active=True
    ).distinct()
    
    return render(request, 'core/chama_list.html', {
        'user_chamas': user_chamas,
        'available_chamas': available_chamas,
    })

@login_required
def chama_create(request):
    if request.method == 'POST':
        form = ChamaForm(request.POST)
        if form.is_valid():
            chama = form.save(commit=False)
            chama.created_by = request.user
            chama.save()
            # Create membership as admin
            Membership.objects.create(
                chama=chama,
                user=request.user,
                role='admin'
            )
            messages.success(request, f'Chama "{chama.name}" created successfully!')
            return redirect('chama_detail', chama_id=chama.id)
    else:
        form = ChamaForm()
    return render(request, 'core/chama_form.html', {'form': form, 'action': 'Create'})

@login_required
def chama_detail(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this Chama.')
        return redirect('chama_list')
    
    # Chama statistics
    total_contributions = Contribution.objects.filter(membership__chama=chama).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    member_count = chama.get_member_count()
    
    # Recent contributions
    recent_contributions = Contribution.objects.filter(
        membership__chama=chama
    ).order_by('-date')[:10]
    
    # Recent transactions
    recent_transactions = Transaction.objects.filter(chama=chama).order_by('-date')[:10]
    
    # Announcements
    chama_announcements = Announcement.objects.filter(chama=chama).order_by('-created_at')[:10]
    
    # Members list
    members = Membership.objects.filter(chama=chama, is_active=True).select_related('user')
    
    context = {
        'chama': chama,
        'membership': membership,
        'total_contributions': total_contributions,
        'member_count': member_count,
        'recent_contributions': recent_contributions,
        'recent_transactions': recent_transactions,
        'announcements': chama_announcements,
        'members': members,
        'can_edit': membership.can_edit_chama(),
        'can_add_transactions': membership.can_add_transactions(),
    }
    
    return render(request, 'core/chama_detail.html', context)

@login_required
def chama_edit(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership or not membership.can_edit_chama():
        messages.error(request, 'You do not have permission to edit this Chama.')
        return redirect('chama_detail', chama_id=chama_id)
    
    if request.method == 'POST':
        form = ChamaForm(request.POST, instance=chama)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chama updated successfully!')
            return redirect('chama_detail', chama_id=chama_id)
    else:
        form = ChamaForm(instance=chama)
    
    return render(request, 'core/chama_form.html', {'form': form, 'chama': chama, 'action': 'Edit'})

@login_required
def chama_join(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id, is_active=True)
    
    # Check if already a member
    existing_membership = Membership.objects.filter(chama=chama, user=request.user).first()
    if existing_membership:
        if existing_membership.is_active:
            messages.info(request, 'You are already a member of this Chama.')
        else:
            existing_membership.is_active = True
            existing_membership.save()
            messages.success(request, f'You have rejoined "{chama.name}"!')
        return redirect('chama_detail', chama_id=chama_id)
    
    # Create new membership
    Membership.objects.create(chama=chama, user=request.user, role='member')
    messages.success(request, f'You have joined "{chama.name}"!')
    return redirect('chama_detail', chama_id=chama_id)

# Contribution Views
@login_required
def contribution_list(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this Chama.')
        return redirect('chama_list')
    
    contributions = Contribution.objects.filter(membership__chama=chama).order_by('-date')
    total = contributions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    return render(request, 'core/contribution_list.html', {
        'chama': chama,
        'membership': membership,
        'contributions': contributions,
        'total': total,
    })

@login_required
def contribution_add(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this Chama.')
        return redirect('chama_list')
    
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.membership = membership
            contribution.save()
            messages.success(request, 'Contribution recorded successfully!')
            return redirect('contribution_list', chama_id=chama_id)
    else:
        form = ContributionForm(initial={'date': timezone.now().date()})
    
    return render(request, 'core/contribution_form.html', {
        'form': form,
        'chama': chama,
        'membership': membership,
    })

# Transaction Views
@login_required
def transaction_list(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this Chama.')
        return redirect('chama_list')
    
    transactions = Transaction.objects.filter(chama=chama).order_by('-date')
    
    return render(request, 'core/transaction_list.html', {
        'chama': chama,
        'membership': membership,
        'transactions': transactions,
    })

@login_required
def transaction_add(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership or not membership.can_add_transactions():
        messages.error(request, 'You do not have permission to add transactions.')
        return redirect('chama_detail', chama_id=chama_id)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.chama = chama
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, 'Transaction recorded successfully!')
            return redirect('transaction_list', chama_id=chama_id)
    else:
        form = TransactionForm(initial={'date': timezone.now().date()})
    
    return render(request, 'core/transaction_form.html', {
        'form': form,
        'chama': chama,
        'membership': membership,
    })

# Announcement Views
@login_required
def announcement_list(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this Chama.')
        return redirect('chama_list')
    
    announcements = Announcement.objects.filter(chama=chama).order_by('-created_at')
    
    return render(request, 'core/announcement_list.html', {
        'chama': chama,
        'membership': membership,
        'announcements': announcements,
    })

@login_required
def announcement_add(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = Membership.objects.filter(chama=chama, user=request.user, is_active=True).first()
    
    if not membership or not membership.can_edit_chama():
        messages.error(request, 'You do not have permission to create announcements.')
        return redirect('chama_detail', chama_id=chama_id)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.chama = chama
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, 'Announcement created successfully!')
            return redirect('announcement_list', chama_id=chama_id)
    else:
        form = AnnouncementForm()
    
    return render(request, 'core/announcement_form.html', {
        'form': form,
        'chama': chama,
        'membership': membership,
    })

# Message Views
@login_required
def message_list(request):
    received_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    sent_messages = Message.objects.filter(sender=request.user).order_by('-created_at')
    unread_count = received_messages.filter(is_read=False).count()
    
    return render(request, 'core/message_list.html', {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'unread_count': unread_count,
    })

@login_required
def message_send(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('message_list')
    else:
        form = MessageForm(user=request.user)
        # Handle reply functionality
        reply_to = request.GET.get('reply_to')
        if reply_to:
            try:
                recipient = User.objects.get(id=reply_to)
                # Check if recipient is in the queryset (user can message them)
                if recipient in form.fields['recipient'].queryset:
                    form.initial['recipient'] = recipient
                    form.initial['subject'] = f"Re: "
            except (User.DoesNotExist, ValueError):
                pass
    
    return render(request, 'core/message_form.html', {'form': form})

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    # Only sender or recipient can view
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('message_list')
    
    # Mark as read if recipient
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
    
    return render(request, 'core/message_detail.html', {'message': message})
