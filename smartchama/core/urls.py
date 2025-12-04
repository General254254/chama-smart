from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Chama
    path('chamas/', views.chama_list, name='chama_list'),
    path('chamas/create/', views.chama_create, name='chama_create'),
    path('chamas/<int:chama_id>/', views.chama_detail, name='chama_detail'),
    path('chamas/<int:chama_id>/edit/', views.chama_edit, name='chama_edit'),
    path('chamas/<int:chama_id>/join/', views.chama_join, name='chama_join'),
    
    # Contributions
    path('chamas/<int:chama_id>/contributions/', views.contribution_list, name='contribution_list'),
    path('chamas/<int:chama_id>/contributions/add/', views.contribution_add, name='contribution_add'),
    
    # Transactions
    path('chamas/<int:chama_id>/transactions/', views.transaction_list, name='transaction_list'),
    path('chamas/<int:chama_id>/transactions/add/', views.transaction_add, name='transaction_add'),
    
    # Announcements
    path('chamas/<int:chama_id>/announcements/', views.announcement_list, name='announcement_list'),
    path('chamas/<int:chama_id>/announcements/add/', views.announcement_add, name='announcement_add'),
    
    # Messages
    path('messages/', views.message_list, name='message_list'),
    path('messages/send/', views.message_send, name='message_send'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
]
