from django.urls import path

from . import views

app_name = "contact"

urlpatterns = [
    path("", views.index, name="index"),
    path("r/<int:pk>/", views.PublicRequestView.as_view(), name="public-request"),
    path("r/<int:pk>/access/", views.public_access_gate, name="public-access-gate"),
    path(
        "attachments/<int:pk>/download/",
        views.AttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
    path("staff/login/", views.StaffLoginView.as_view(), name="staff-login"),
    path("staff/logout/", views.StaffLogoutView.as_view(), name="staff-logout"),
    path("staff/requests/", views.StaffRequestListView.as_view(), name="staff-request-list"),
    path(
        "staff/requests/<int:pk>/",
        views.StaffRequestDetailView.as_view(),
        name="staff-request-detail",
    ),
    path("staff/users/", views.StaffUserManagementView.as_view(), name="staff-user-list"),
]
