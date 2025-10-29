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
    path('requests/', views.user_requests, name='user_requests'),
    path('requests/restore/', views.restore_access, name='restore_access'),
    path('requests/<int:message_id>/detail/', views.user_message_detail, name='user_message_detail'),
    path('requests/<int:message_id>/update/', views.user_update_message, name='user_update_message'),
    path('requests/<int:message_id>/delete/', views.user_delete_message, name='user_delete_message'),
]
