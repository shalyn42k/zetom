from __future__ import annotations

from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # варианты компаний для селекта
    COMPANY_CHOICES = [
        ("firma1", "Firma 1"),
        ("firma2", "Firma 2"),
        ("firma3", "Firma 3"),
        ("inna",   "Inna"),
    ]

    # переопределяем поле модели как ChoiceField
    company = forms.ChoiceField(
        choices=COMPANY_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-input"})
    )

    class Meta:
        model = ContactMessage
        fields = ["first_name", "last_name", "phone", "email", "company", "message"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "message": forms.Textarea(attrs={"rows": 5, "class": "form-input"}),
        }


class LoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))


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
        widget=forms.CheckboxSelectMultiple
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
        widget=forms.CheckboxSelectMultiple,
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
