"""
# === FILE SUMMARY ===
# Purpose: URL routing for the contact application.
# Responsible for: Mapping public, authentication, admin, and user portal endpoints to view functions.
# Connected to: contact.views module functions (index, login, logout, panel, message management).
# Important classes/functions: urlpatterns list
# Notes: Includes aliases and nested paths for admin and user workflows.
# =====================================
"""

from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index_alias'),  # ← добавили
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('panel/', views.panel, name='panel'),
    path('panel/messages/<int:message_id>/detail/', views.message_detail, name='message_detail'),
    path('panel/messages/<int:message_id>/update/', views.update_message, name='update_message'),
    path(
        'panel/messages/<int:message_id>/logs/<int:log_id>/rollback/',
        views.rollback_client_change,
        name='rollback_client_change',
    ),
    path('panel/settings/', views.admin_settings, name='admin_settings'),
    path('panel/reset-password/', views.admin_reset_password, name='admin_reset_password'),
    path('panel/profile/', views.admin_profile, name='admin_profile'),
    path('panel/verify-password/', views.admin_verify_password, name='admin_verify_password'),
    path('requests/', views.user_requests, name='user_requests'),
    path('requests/restore/', views.restore_access, name='restore_access'),
    path('requests/<int:message_id>/detail/', views.user_message_detail, name='user_message_detail'),
    path('requests/<int:message_id>/update/', views.user_update_message, name='user_update_message'),
    path('requests/<int:message_id>/delete/', views.user_delete_message, name='user_delete_message'),
]
