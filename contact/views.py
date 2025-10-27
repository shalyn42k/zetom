from __future__ import annotations

from datetime import datetime
from typing import Iterable

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, TemplateView

from .forms import (
    ContactForm,
    PublicAccessForm,
    PublicRequestUpdateForm,
    StaffDepartmentFilterForm,
    StaffRequestUpdateForm,
    StaffUserForm,
)
from .models import Activity, Attachment, Request, StaffProfile
from .permissions import get_staff_profile, user_can_edit_request, user_can_view_request
from .services.activity import log_activity
from .utils import get_language

User = get_user_model()


def _store_attachments(
    *,
    request_obj: Request,
    attachments: Iterable[tuple],
    uploaded_by: User | None,
    public: bool,
) -> None:
    for upload, content_type, size in attachments:
        stored = Attachment.objects.create(
            request=request_obj,
            file=upload,
            original_name=upload.name,
            size=size,
            content_type=content_type,
            uploaded_by=uploaded_by if uploaded_by and uploaded_by.is_authenticated else None,
        )
        log_activity(
            request_obj=request_obj,
            activity_type=Activity.Type.FILE_UPLOAD,
            actor=uploaded_by if uploaded_by and uploaded_by.is_authenticated else None,
            message=f"Uploaded {stored.original_name}",
            is_public=public,
            meta={"attachment_id": stored.pk, "content_type": content_type},
        )


def _session_access_key(request_obj: Request) -> str:
    return f"request-access::{request_obj.pk}"


@require_http_methods(["GET", "POST"])
def index(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = ContactForm(request.POST or None, request.FILES or None, language=lang)
    success_data = request.session.pop("contact_request_info", None)

    if request.method == "POST" and form.is_valid():
        request_obj: Request = form.save(commit=False)
        if request.user.is_authenticated:
            request_obj.created_by = request.user
        request_obj.save()

        attachments = form.cleaned_data.get("attachments", [])
        if attachments:
            _store_attachments(
                request_obj=request_obj,
                attachments=attachments,
                uploaded_by=request.user if request.user.is_authenticated else None,
                public=False,
            )

        log_activity(
            request_obj=request_obj,
            activity_type=Activity.Type.SYSTEM,
            actor=request.user if request.user.is_authenticated else None,
            message="Request created",
            is_public=True,
            meta={"status": request_obj.status},
        )

        success_message = (
            "Wiadomość została wysłana. Zostanie przetworzona w ciągu 48 godzin, po czym się z Tobą skontaktujemy."
            if lang == "pl"
            else "Your request has been sent. We will process it within 48 hours and contact you afterwards."
        )
        messages.success(request, success_message)

        session_payload = {"id": request_obj.pk}
        if not request.user.is_authenticated:
            session_payload["token"] = request_obj.access_token
        request.session["contact_request_info"] = session_payload

        return redirect(f"{reverse('contact:index')}?lang={lang}")

    activity_feed = Activity.objects.filter(is_public=True).order_by("-created_at")[:5]

    context = {
        "form": form,
        "lang": lang,
        "success_info": success_data,
        "activity_feed": activity_feed,
    }
    return render(request, "contact/index.html", context)


class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        profile = get_staff_profile(request.user)
        if not profile:
            raise PermissionDenied
        request.staff_profile = profile
        return super().dispatch(request, *args, **kwargs)


class StaffLoginView(LoginView):
    template_name = "contact/staff/login.html"
    redirect_authenticated_user = True


class StaffLogoutView(LogoutView):
    next_page = reverse_lazy("contact:staff-login")


class StaffRequestListView(StaffRequiredMixin, ListView):
    model = Request
    context_object_name = "requests"
    template_name = "contact/staff/request_list.html"
    paginate_by = 20

    def get_queryset(self):
        profile = get_staff_profile(self.request.user)
        queryset = (
            Request.objects.filter(is_deleted=False)
            .select_related("department")
            .order_by("-created_at")
        )
        self.filter_form = StaffDepartmentFilterForm(self.request.GET)
        self.filter_form.is_valid()
        if profile and profile.role == StaffProfile.Role.EMPLOYEE:
            queryset = queryset.filter(department=profile.department)
        else:
            department = self.filter_form.cleaned_data.get("department")
            if department:
                queryset = queryset.filter(department=department)
        status = self.filter_form.cleaned_data.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["profile"] = get_staff_profile(self.request.user)
        return context


class StaffRequestDetailView(StaffRequiredMixin, View):
    template_name = "contact/staff/request_detail.html"

    def get_request_object(self) -> Request:
        request_obj = get_object_or_404(Request.objects.select_related("department"), pk=self.kwargs["pk"])
        if not user_can_view_request(self.request.user, request_obj):
            raise PermissionDenied
        return request_obj

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        request_obj = self.get_request_object()
        form = StaffRequestUpdateForm(instance=request_obj, user=request.user)
        context = self._build_context(request_obj, form)
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        request_obj = self.get_request_object()
        action = request.POST.get("action")

        if action == "reset_access":
            new_token = request_obj.issue_access_token()
            log_activity(
                request_obj=request_obj,
                activity_type=Activity.Type.SYSTEM,
                actor=request.user,
                message="Access link reset",
                is_public=False,
            )
            messages.success(request, _("Access link has been reset. New token: %s") % new_token)
            return redirect("contact:staff-request-detail", pk=request_obj.pk)

        form = StaffRequestUpdateForm(
            request.POST,
            request.FILES,
            instance=request_obj,
            user=request.user,
        )
        if not form.is_valid():
            context = self._build_context(request_obj, form)
            return render(request, self.template_name, context)

        if not user_can_edit_request(request.user, request_obj):
            raise PermissionDenied

        previous_status = request_obj.status
        previous_department = request_obj.department_id
        previous_access = request_obj.access_enabled

        form.save()

        attachments = form.cleaned_data.get("attachments", [])
        if attachments:
            _store_attachments(
                request_obj=request_obj,
                attachments=attachments,
                uploaded_by=request.user,
                public=False,
            )

        if previous_status != request_obj.status:
            log_activity(
                request_obj=request_obj,
                activity_type=Activity.Type.STATUS_CHANGE,
                actor=request.user,
                message=f"Status changed to {request_obj.status}",
                is_public=False,
                meta={"from": previous_status, "to": request_obj.status},
            )

        if previous_department != request_obj.department_id:
            log_activity(
                request_obj=request_obj,
                activity_type=Activity.Type.ASSIGNMENT,
                actor=request.user,
                message="Department reassigned",
                is_public=False,
                meta={"department_id": request_obj.department_id},
            )

        if previous_access != request_obj.access_enabled:
            state = "enabled" if request_obj.access_enabled else "disabled"
            log_activity(
                request_obj=request_obj,
                activity_type=Activity.Type.SYSTEM,
                actor=request.user,
                message=f"Access {state}",
                is_public=False,
            )

        messages.success(request, _("Request updated."))
        return redirect("contact:staff-request-detail", pk=request_obj.pk)

    def _build_context(self, request_obj: Request, form: StaffRequestUpdateForm) -> dict:
        return {
            "request_obj": request_obj,
            "update_form": form,
            "attachments": request_obj.attachments.all(),
            "activities": request_obj.activities.order_by("-created_at"),
            "profile": get_staff_profile(self.request.user),
        }


class StaffUserManagementView(StaffRequiredMixin, TemplateView):
    template_name = "contact/staff/user_list.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        profile = get_staff_profile(request.user)
        if not (profile and profile.role == StaffProfile.Role.ADMIN):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = []
        for user in (
            User.objects.filter(is_active=True)
            .order_by("username")
            .select_related("staff_profile", "staff_profile__department")
        ):
            profile = getattr(user, "staff_profile", None)
            if profile is None:
                profile = StaffProfile(user=user, role=StaffProfile.Role.EMPLOYEE)
            records.append({"user": user, "form": StaffUserForm(instance=profile)})
        context.update({"records": records})
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user_id = request.POST.get("user_id")
        if not user_id:
            raise Http404
        target_user = get_object_or_404(User, pk=user_id)
        profile, _ = StaffProfile.objects.get_or_create(
            user=target_user,
            defaults={"role": StaffProfile.Role.EMPLOYEE},
        )
        form = StaffUserForm(request.POST, instance=profile)
        if form.is_valid():
            updated_profile = form.save()
            messages.success(
                request,
                _("Profile for %s updated.") % target_user.get_username(),
            )
        else:
            messages.error(request, _("Unable to update profile."))
        return redirect("contact:staff-user-list")


class PublicRequestView(View):
    template_name = "contact/public_request_detail.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.request_obj = get_object_or_404(Request, pk=kwargs["pk"], is_deleted=False)
        return super().dispatch(request, *args, **kwargs)

    def _grant_session_access(self, request: HttpRequest) -> None:
        request.session[_session_access_key(self.request_obj)] = timezone.now().isoformat()

    def _has_session_access(self, request: HttpRequest) -> bool:
        return _session_access_key(self.request_obj) in request.session

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not self.request_obj.access_enabled:
            return HttpResponseForbidden("Access disabled")

        access_token = request.GET.get("access")
        if access_token and self.request_obj.verify_access_token(access_token):
            if not self.request_obj.access_enabled:
                return HttpResponseForbidden("Access disabled")
            self._grant_session_access(request)
            return redirect("contact:public-request", pk=self.request_obj.pk)

        if not self._has_session_access(request):
            form = PublicAccessForm(initial={"request_id": self.request_obj.pk})
            return render(
                request,
                "contact/public_request_gate.html",
                {"form": form, "request_obj": self.request_obj},
            )

        context = self._build_context(request)
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not getattr(settings, "ALLOW_PUBLIC_EDITS", False):
            raise PermissionDenied
        if not self._has_session_access(request):
            form = PublicAccessForm(request.POST)
            if form.is_valid():
                token = form.cleaned_data["access_token"]
                if self.request_obj.verify_access_token(token):
                    if not self.request_obj.access_enabled:
                        return HttpResponseForbidden("Access disabled")
                    self._grant_session_access(request)
                    return redirect("contact:public-request", pk=self.request_obj.pk)
            return render(
                request,
                "contact/public_request_gate.html",
                {"form": form, "request_obj": self.request_obj},
            )

        if not self.request_obj.access_enabled:
            return HttpResponseForbidden("Access disabled")

        cooldown = getattr(settings, "PUBLIC_EDIT_RATE_LIMIT_SECONDS", 60)
        last_edit_key = f"public-edit::{self.request_obj.pk}"
        last_edit = request.session.get(last_edit_key)
        now = timezone.now()
        if last_edit:
            last_dt = datetime.fromisoformat(last_edit)
            if (now - last_dt).total_seconds() < cooldown:
                messages.error(request, _("Please wait before submitting another update."))
                context = self._build_context(request)
                return render(request, self.template_name, context)

        form = PublicRequestUpdateForm(request.POST, request.FILES, instance=self.request_obj)
        if not form.is_valid():
            context = self._build_context(request)
            context["public_form"] = form
            return render(request, self.template_name, context)

        form.save()
        attachments = form.cleaned_data.get("attachments", [])
        if attachments:
            _store_attachments(
                request_obj=self.request_obj,
                attachments=attachments,
                uploaded_by=None,
                public=True,
            )

        log_activity(
            request_obj=self.request_obj,
            activity_type=Activity.Type.COMMENT,
            actor=None,
            message="Public update submitted",
            is_public=True,
        )

        request.session[last_edit_key] = now.isoformat()
        messages.success(request, _("Update received."))
        return redirect("contact:public-request", pk=self.request_obj.pk)

    def _build_context(self, request: HttpRequest) -> dict:
        context = {
            "request_obj": self.request_obj,
            "attachments": self.request_obj.attachments.all(),
            "activities": self.request_obj.activities.filter(is_public=True).order_by("-created_at"),
            "public_edit_enabled": getattr(settings, "ALLOW_PUBLIC_EDITS", False),
        }
        if getattr(settings, "ALLOW_PUBLIC_EDITS", False):
            context["public_form"] = PublicRequestUpdateForm(instance=self.request_obj)
        return context


class AttachmentDownloadView(View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        attachment = get_object_or_404(Attachment.objects.select_related("request"), pk=pk)
        request_obj = attachment.request

        token = request.GET.get("access")
        has_access = False
        if request.user.is_authenticated and user_can_view_request(request.user, request_obj):
            has_access = True
        elif token and request_obj.verify_access_token(token):
            has_access = True
        elif _session_access_key(request_obj) in request.session:
            has_access = True

        if not has_access:
            raise PermissionDenied

        if not request_obj.access_enabled and not (
            request.user.is_authenticated and user_can_view_request(request.user, request_obj)
        ):
            raise PermissionDenied

        file_handle = attachment.file.open("rb")
        response = FileResponse(file_handle, as_attachment=True, filename=attachment.original_name)
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Type"] = attachment.content_type
        return response


@require_http_methods(["POST"])
def public_access_gate(request: HttpRequest, pk: int) -> HttpResponse:
    request_obj = get_object_or_404(Request, pk=pk, is_deleted=False)
    form = PublicAccessForm(request.POST)
    if form.is_valid():
        if form.cleaned_data["request_id"] != request_obj.pk:
            form.add_error("request_id", _("Request not found."))
        elif request_obj.verify_access_token(form.cleaned_data["access_token"]):
            if not request_obj.access_enabled:
                return HttpResponseForbidden("Access disabled")
            request.session[_session_access_key(request_obj)] = timezone.now().isoformat()
            return redirect("contact:public-request", pk=request_obj.pk)
        else:
            form.add_error("access_token", _("Invalid token."))

    return render(
        request,
        "contact/public_request_gate.html",
        {"form": form, "request_obj": request_obj},
    )

