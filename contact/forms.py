from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Department, Request, StaffProfile
from .utils.attachments import validate_uploads

User = get_user_model()


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    widget = MultiFileInput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs.setdefault("multiple", True)

    def clean(self, data, initial=None):
        if data is None:
            files = []
        elif hasattr(data, "getlist"):
            files = data.getlist(self.name)
        elif isinstance(data, (list, tuple)):
            files = list(data)
        elif data:
            files = [data]
        else:
            files = []

        cleaned = validate_uploads(files, allow_empty=not self.required)
        self.run_validators(cleaned)
        return cleaned


class ContactForm(forms.ModelForm):
    COMPANY_CHOICES = [
        ("firma1", "Firma 1"),
        ("firma2", "Firma 2"),
        ("firma3", "Firma 3"),
        ("inna", "Inna"),
    ]

    bot_check = forms.BooleanField(
        required=False,
        label="",
        widget=forms.CheckboxInput(
            attrs={"class": "form-checkbox-input", "data-bot-check": "true"}
        ),
    )
    attachments = MultiFileField(required=False)

    company = forms.ChoiceField(
        choices=COMPANY_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-input",
                "data-review-source": "company",
            }
        ),
    )

    def __init__(self, *args, language: str | None = None, **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)
        message = (
            "Potwierdź, że nie jesteś botem."
            if self.language == "pl"
            else "Please confirm you are not a bot."
        )
        self.fields["bot_check"].error_messages["required"] = message
        self.fields["attachments"].widget.attrs.update({
            "class": "form-input",
            "data-review-source": "attachments",
            "multiple": True,
        })

    class Meta:
        model = Request
        fields = ["first_name", "last_name", "phone", "email", "company", "message"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-input", "data-review-source": "first_name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-input", "data-review-source": "last_name"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-input", "data-review-source": "phone"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-input", "data-review-source": "email"}
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "form-input",
                    "data-review-source": "message",
                }
            ),
        }

    def clean_bot_check(self) -> bool:
        bot_check = self.cleaned_data.get("bot_check")
        if not bot_check:
            message = (
                "Potwierdź, że nie jesteś botem."
                if self.language == "pl"
                else "Please confirm you are not a bot."
            )
            raise forms.ValidationError(message)
        return bot_check


class PublicAccessForm(forms.Form):
    request_id = forms.IntegerField(label=_("Request ID"))
    access_token = forms.CharField(label=_("Access token"))


class PublicRequestUpdateForm(forms.ModelForm):
    attachments = MultiFileField(required=False)

    class Meta:
        model = Request
        fields = ["final_changes"]
        widgets = {
            "final_changes": forms.Textarea(attrs={"rows": 5, "class": "form-input"})
        }


class StaffRequestUpdateForm(forms.ModelForm):
    attachments = MultiFileField(required=False)

    class Meta:
        model = Request
        fields = [
            "status",
            "final_response",
            "final_changes",
            "access_enabled",
            "department",
        ]
        widgets = {
            "final_response": forms.Textarea(attrs={"rows": 4, "class": "form-input"}),
            "final_changes": forms.Textarea(attrs={"rows": 3, "class": "form-input"}),
        }

    def __init__(self, *args, user: User | None = None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["attachments"].widget.attrs.update({
            "class": "form-input",
            "multiple": True,
        })
        if not user:
            self.fields.pop("department")
            return
        profile = getattr(user, "staff_profile", None)
        if not (profile and profile.role == StaffProfile.Role.ADMIN) and not user.is_superuser:
            self.fields.pop("department")


class StaffDepartmentFilterForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        empty_label=_("All departments"),
    )
    status = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.filter(is_active=True)
        choices = [("", _("All statuses"))]
        for value, label in Request.STATUS_CHOICES:
            choices.append((value, label))
        self.fields["status"].choices = choices


class StaffUserForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ["role", "department"]
        widgets = {
            "department": forms.Select(attrs={"class": "form-input"}),
            "role": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].required = False

