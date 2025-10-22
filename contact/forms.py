from __future__ import annotations

from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    COMPANY_CHOICES = [
        ("firma1", "Firma 1"),
        ("firma2", "Firma 2"),
        ("firma3", "Firma 3"),
        ("inna",   "Inna"),
    ]

    bot_check = forms.BooleanField(
        required=False,
        label="",
        widget=forms.CheckboxInput(attrs={"class": "form-checkbox-input", "data-bot-check": "true"}),
    )

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

    class Meta:
        model = ContactMessage
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


class LoginForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input login-input"})
    )


class MessageBulkActionForm(forms.Form):
    ACTION_MARK_NEW = "mark_new"
    ACTION_MARK_IN_PROGRESS = "mark_in_progress"
    ACTION_MARK_READY = "mark_ready"
    ACTION_DELETE = "delete"

    ACTION_CHOICES = (
        (ACTION_MARK_NEW, "Mark as new"),
        (ACTION_MARK_IN_PROGRESS, "Mark as in progress"),
        (ACTION_MARK_READY, "Mark as ready"),
        (ACTION_DELETE, "Delete"),
    )

    action = forms.ChoiceField(choices=ACTION_CHOICES)
    selected = forms.MultipleChoiceField(
        choices=(),
        required=True,
        widget=forms.CheckboxSelectMultiple(),  # стандартный виджет
    )

    def __init__(self, *args, message_choices: list[tuple[str, str]] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["selected"].choices = message_choices or []
        self.fields["action"].widget.attrs["class"] = "form-input"


class TrashActionForm(forms.Form):
    ACTION_RESTORE = "restore"
    ACTION_DELETE = "delete"
    ACTION_EMPTY = "empty"

    ACTION_CHOICES = (
        (ACTION_RESTORE, "restore"),
        (ACTION_DELETE, "delete"),
        (ACTION_EMPTY, "empty"),
    )

    form_name = forms.CharField(widget=forms.HiddenInput(), initial="trash")
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    selected = forms.MultipleChoiceField(
        choices=(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),  # стандартный виджет
    )

    def __init__(
        self,
        *args,
        message_choices: list[tuple[str, str]] | None = None,
        language: str | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields["selected"].choices = message_choices or []
        # action управляется кнопками — прячем поле
        self.fields["action"].widget = forms.HiddenInput()
        self._empty_selection_message = (
            "Wybierz co najmniej jedną wiadomość."
            if language == "pl"
            else "Select at least one message."
        )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get("action")
        selected = cleaned_data.get("selected") or []
        if action in {self.ACTION_RESTORE, self.ACTION_DELETE} and not selected:
            raise forms.ValidationError(self._empty_selection_message)
        return cleaned_data


class EmailForm(forms.Form):
    to_email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-input"}))
    subject = forms.CharField(
        max_length=255,
        initial="Custom message",
        widget=forms.TextInput(attrs={"class": "form-input"})
    )
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 6, "class": "form-input"}))
    attachment = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-input"}))


class MessageFilterForm(forms.Form):
    SORT_NEWEST = "newest"
    SORT_OLDEST = "oldest"
    SORT_STATUS = "status"
    SORT_COMPANY = "company"

    COMPANY_ALL = "all"

    SORT_CHOICES = (
        (SORT_NEWEST, "Newest first"),
        (SORT_OLDEST, "Oldest first"),
        (SORT_STATUS, "Status"),
        (SORT_COMPANY, "Company"),
    )

    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False)
    company = forms.ChoiceField(choices=(), required=False)

    def __init__(self, *args, language: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        company_choices = [(self.COMPANY_ALL, "All departments")] + list(ContactForm.COMPANY_CHOICES)
        if language == "pl":
            sort_labels = {
                self.SORT_NEWEST: "Najnowsze",
                self.SORT_OLDEST: "Najstarsze",
                self.SORT_STATUS: "Status",
                self.SORT_COMPANY: "Firma",
            }
            company_labels = {
                self.COMPANY_ALL: "Wszystkie departamenty",
                "firma1": "Firma 1",
                "firma2": "Firma 2",
                "firma3": "Firma 3",
                "inna": "Inna",
            }
        else:
            sort_labels = {
                self.SORT_NEWEST: "Newest first",
                self.SORT_OLDEST: "Oldest first",
                self.SORT_STATUS: "Status",
                self.SORT_COMPANY: "Company",
            }
            company_labels = {
                self.COMPANY_ALL: "All departments",
                "firma1": "Company 1",
                "firma2": "Company 2",
                "firma3": "Company 3",
                "inna": "Other",
            }

        self.fields["sort_by"].choices = [
            (value, sort_labels.get(value, label)) for value, label in self.SORT_CHOICES
        ]
        self.fields["company"].choices = [
            (value, company_labels.get(value, label)) for value, label in company_choices
        ]
        self.fields["sort_by"].widget.attrs["class"] = "form-input"
        self.fields["company"].widget.attrs["class"] = "form-input"
        self.fields["sort_by"].initial = self.SORT_NEWEST
        self.fields["company"].initial = self.COMPANY_ALL

    def clean_sort_by(self) -> str:
        value = self.cleaned_data.get("sort_by") or self.SORT_NEWEST
        valid_values = {choice[0] for choice in self.fields["sort_by"].choices}
        if value not in valid_values:
            return self.SORT_NEWEST
        return value

    def clean_company(self) -> str:
        value = self.cleaned_data.get("company") or self.COMPANY_ALL
        valid_values = {choice[0] for choice in self.fields["company"].choices}
        if value not in valid_values:
            return self.COMPANY_ALL
        return value


class DownloadMessagesForm(forms.Form):
    FIELD_CREATED_AT = "created_at"
    FIELD_CUSTOMER = "customer"
    FIELD_PHONE = "phone"
    FIELD_EMAIL = "email"
    FIELD_COMPANY = "company"
    FIELD_MESSAGE = "message"
    FIELD_STATUS = "status"

    FIELD_CHOICES = (
        (FIELD_CREATED_AT, "Created at"),
        (FIELD_CUSTOMER, "Customer"),
        (FIELD_PHONE, "Phone"),
        (FIELD_EMAIL, "Email"),
        (FIELD_COMPANY, "Company"),
        (FIELD_MESSAGE, "Message"),
        (FIELD_STATUS, "Status"),
    )

    form_name = forms.CharField(widget=forms.HiddenInput(), initial="download")
    messages = forms.MultipleChoiceField(
        choices=(),
        widget=forms.MultipleHiddenInput(),
        required=True,
    )
    fields = forms.MultipleChoiceField(
        choices=FIELD_CHOICES,
        widget=forms.CheckboxSelectMultiple(),   # стандартный виджет
        required=True,
    )

    def __init__(
        self,
        *args,
        message_choices: list[tuple[str, str]] | None = None,
        language: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fields["messages"].choices = message_choices or []

        if language == "pl":
            field_labels = {
                self.FIELD_CREATED_AT: "Data zgłoszenia",
                self.FIELD_CUSTOMER: "Klient",
                self.FIELD_PHONE: "Telefon",
                self.FIELD_EMAIL: "E-mail",
                self.FIELD_COMPANY: "Firma",
                self.FIELD_MESSAGE: "Wiadomość",
                self.FIELD_STATUS: "Status",
            }
            self._messages_error = "Wybierz co najmniej jedno zgłoszenie."
            self._fields_error = "Wybierz co najmniej jedno pole."
        else:
            field_labels = {
                self.FIELD_CREATED_AT: "Submitted at",
                self.FIELD_CUSTOMER: "Customer",
                self.FIELD_PHONE: "Phone",
                self.FIELD_EMAIL: "Email",
                self.FIELD_COMPANY: "Company",
                self.FIELD_MESSAGE: "Message",
                self.FIELD_STATUS: "Status",
            }
            self._messages_error = "Select at least one request."
            self._fields_error = "Select at least one field."

        self.fields["fields"].choices = [
            (value, field_labels.get(value, label)) for value, label in self.FIELD_CHOICES
        ]

        # data-* атрибуты для JS (не обяз.)
        self.fields["fields"].widget.attrs.update({"data-download-field": "true"})

        # По умолчанию — все поля отмечены
        if not self.is_bound:
            self.fields["fields"].initial = [value for value, _ in self.fields["fields"].choices]

    def clean_messages(self) -> list[str]:
        data = self.cleaned_data.get("messages") or []
        if not data:
            raise forms.ValidationError(self._messages_error)
        return data

    def clean_fields(self) -> list[str]:
        data = self.cleaned_data.get("fields") or []
        if not data:
            raise forms.ValidationError(self._fields_error)
        return data


class MessageUpdateForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "company",
            "message",
            "status",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "company": forms.Select(attrs={"class": "form-input"}),
            "message": forms.Textarea(attrs={"rows": 6, "class": "form-input"}),
            "status": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].choices = ContactForm.COMPANY_CHOICES
        self.fields["status"].choices = ContactMessage.STATUS_CHOICES


class UserMessageUpdateForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "company",
            "message",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "company": forms.Select(attrs={"class": "form-input"}),
            "message": forms.Textarea(attrs={"rows": 5, "class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].choices = ContactForm.COMPANY_CHOICES
