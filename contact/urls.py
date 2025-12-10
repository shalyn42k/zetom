"""
# === FILE SUMMARY ===
# Purpose: URL routing for the contact application.
# Responsible for: Mapping public, authentication, admin, and user portal endpoints to view functions.
# Connected to: contact.views module functions (index, login, logout, panel, message management).
# Important classes/functions: urlpatterns list
# Notes: Includes aliases and nested paths for admin and user workflows.
# =====================================
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index_alias'),  # ← добавили
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('requests/access/', views.access_portal, name='access_portal'),
    path('panel/', login_required(views.panel, login_url='/login/'), name='panel'),
    path(
        'panel/messages/<int:message_id>/detail/',
        login_required(views.message_detail, login_url='/login/'),
        name='message_detail',
    ),
    path(
        'panel/messages/<int:message_id>/update/',
        login_required(views.update_message, login_url='/login/'),
        name='update_message',
    ),
    path(
        'panel/messages/<int:message_id>/logs/<int:log_id>/rollback/',
        login_required(views.rollback_client_change, login_url='/login/'),
        name='rollback_client_change',
    ),
    path(
        'panel/api/users/<int:user_id>/settings/',
        login_required(views.admin_user_settings, login_url='/login/'),
        name='admin_user_settings',
    ),
    path('panel/settings/', login_required(views.admin_settings, login_url='/login/'), name='admin_settings'),
    path(
        'panel/reset-password/',
        login_required(views.admin_reset_password, login_url='/login/'),
        name='admin_reset_password',
    ),
    path('panel/profile/', login_required(views.admin_profile, login_url='/login/'), name='admin_profile'),
    path(
        'panel/verify-password/',
        login_required(views.admin_verify_password, login_url='/login/'),
        name='admin_verify_password',
    ),
    path('requests/', views.user_requests, name='user_requests'),
    path('requests/restore/', views.restore_access, name='restore_access'),
    path('requests/<int:message_id>/detail/', views.user_message_detail, name='user_message_detail'),
    path('requests/<int:message_id>/update/', views.user_update_message, name='user_update_message'),
    path('requests/<int:message_id>/delete/', views.user_delete_message, name='user_delete_message'),
]
