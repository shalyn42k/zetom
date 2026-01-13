"""
# === FILE SUMMARY ===
# Purpose: URL routing for the contact application.
# Responsible for: Mapping public, authentication, and admin endpoints to view functions.
# Connected to: contact.views module functions (index, login, logout, panel, message management).
# Important classes/functions: urlpatterns list
# Notes: Includes aliases and nested paths for admin workflows.
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
]
