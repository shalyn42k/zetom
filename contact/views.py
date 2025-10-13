from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    ContactForm,
    EmailForm,
    LoginForm,
    MessageBulkActionForm,
    TrashActionForm,
)
from .services import messages as message_service
from .services.email_service import send_contact_email, send_email_with_attachment
from .utils import get_language


@require_http_methods(['GET', 'POST'])
def index(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = ContactForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        message = message_service.add_message(**form.cleaned_data)
        if settings.SMTP_USER:
            send_contact_email(form.cleaned_data['email'], message)
        success_message = (
            'Wiadomość została wysłana. Skontaktujemy się w ciągu 24 godzin.'
            if lang == 'pl'
            else 'Message sent. We will get back to you within 24 hours.'
        )
        messages.success(request, success_message)
        return redirect(f"{reverse('contact:index')}?lang={lang}")

    context = {
        'form': form,
        'lang': lang,
    }
    return render(request, 'contact/index.html', context)


@require_http_methods(['GET', 'POST'])
def login(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['password'] == settings.ADMIN_PASSWORD:
            request.session['logged_in'] = True
            return redirect('contact:panel')
        error_message = 'Nieprawidłowe hasło!' if lang == 'pl' else 'Wrong password!'
        form.add_error('password', error_message)

    return render(request, 'contact/admin_login.html', {'form': form, 'lang': lang})


@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    lang = request.session.get('lang', settings.DEFAULT_LANGUAGE)
    request.session.flush()
    return redirect(f"{reverse('contact:index')}?lang={lang}")


@require_http_methods(['GET', 'POST'])
def panel(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    if not request.session.get('logged_in'):
        return redirect(f"{reverse('contact:login')}?lang={lang}")

    queryset = message_service.get_messages()
    deleted_queryset = message_service.get_deleted_messages()

    choices = [(str(message.id), f"#{message.id}") for message in queryset]
    deleted_choices = [
        (str(message.id), f"#{message.id} · {message.email}") for message in deleted_queryset
    ]

    action_form = MessageBulkActionForm(request.POST or None, message_choices=choices)
    _localise_action_choices(action_form, lang)
    email_form = EmailForm()
    trash_form = TrashActionForm(message_choices=deleted_choices, language=lang)

    if request.method == 'POST':
        form_name = request.POST.get('form_name')
        if form_name == 'bulk':
            action_form = MessageBulkActionForm(request.POST, message_choices=choices)
            _localise_action_choices(action_form, lang)
            if action_form.is_valid():
                ids = [int(pk) for pk in action_form.cleaned_data['selected']]
                _handle_action(action_form.cleaned_data['action'], ids, lang, request)
                return redirect('contact:panel')
        elif form_name == 'trash':
            trash_form = TrashActionForm(request.POST, message_choices=deleted_choices, language=lang)
            if trash_form.is_valid():
                ids = [int(pk) for pk in trash_form.cleaned_data['selected']]
                _handle_trash_action(trash_form.cleaned_data['action'], ids, lang, request)
                return redirect('contact:panel')
        else:
            email_form = EmailForm(request.POST, request.FILES)
            if email_form.is_valid():
                file = request.FILES.get('attachment')
                send_email_with_attachment(
                    to_email=email_form.cleaned_data['to_email'],
                    subject=email_form.cleaned_data['subject'],
                    body=email_form.cleaned_data['body'],
                    attachment=file,
                    filename=file.name if file else None,
                )
                success_message = 'E-mail został wysłany.' if lang == 'pl' else 'Email sent.'
                messages.success(request, success_message)
                return redirect('contact:panel')

    context = {
        'lang': lang,
        'messages_list': queryset,
        'deleted_messages': deleted_queryset,
        'action_form': action_form,
        'email_form': email_form,
        'trash_form': trash_form,
    }
    return render(request, 'contact/admin_panel.html', context)


def _handle_action(action: str, ids: Iterable[int], lang: str, request: HttpRequest) -> None:
    if action == MessageBulkActionForm.ACTION_MARK_NEW:
        message_service.mark_messages_new(ids)
        text = (
            'Zaznaczone wiadomości oznaczono jako nowe.'
            if lang == 'pl'
            else 'Selected messages marked as new.'
        )
    elif action == MessageBulkActionForm.ACTION_MARK_IN_PROGRESS:
        message_service.mark_messages_in_progress(ids)
        text = (
            'Zaznaczone wiadomości oznaczono jako w trakcie.'
            if lang == 'pl'
            else 'Selected messages marked as in progress.'
        )
    elif action == MessageBulkActionForm.ACTION_MARK_READY:
        message_service.mark_messages_ready(ids)
        text = (
            'Zaznaczone wiadomości oznaczono jako gotowe.'
            if lang == 'pl'
            else 'Selected messages marked as ready.'
        )
    else:
        message_service.delete_messages(ids)
        text = (
            'Zaznaczone wiadomości przeniesiono do kosza.'
            if lang == 'pl'
            else 'Selected messages moved to trash.'
        )
    messages.success(request, text)


def _handle_trash_action(action: str, ids: Iterable[int], lang: str, request: HttpRequest) -> None:
    if action == TrashActionForm.ACTION_RESTORE:
        message_service.restore_messages(ids)
        text = (
            'Wybrane wiadomości przywrócono.'
            if lang == 'pl'
            else 'Selected messages restored.'
        )
    elif action == TrashActionForm.ACTION_DELETE:
        message_service.purge_messages(ids)
        text = (
            'Wybrane wiadomości usunięto bezpowrotnie.'
            if lang == 'pl'
            else 'Selected messages permanently deleted.'
        )
    else:
        message_service.purge_messages()
        text = (
            'Kosz opróżniono.'
            if lang == 'pl'
            else 'Trash emptied.'
        )
    messages.success(request, text)


def _localise_action_choices(form: MessageBulkActionForm, lang: str) -> None:
    if lang == 'pl':
        form.fields['action'].choices = [
            (MessageBulkActionForm.ACTION_MARK_NEW, 'Oznacz jako nowe'),
            (MessageBulkActionForm.ACTION_MARK_IN_PROGRESS, 'Oznacz jako w trakcie'),
            (MessageBulkActionForm.ACTION_MARK_READY, 'Oznacz jako gotowe'),
            (MessageBulkActionForm.ACTION_DELETE, 'Usuń'),
        ]
    else:
        form.fields['action'].choices = [
            (MessageBulkActionForm.ACTION_MARK_NEW, 'Mark as new'),
            (MessageBulkActionForm.ACTION_MARK_IN_PROGRESS, 'Mark as in progress'),
            (MessageBulkActionForm.ACTION_MARK_READY, 'Mark as ready'),
            (MessageBulkActionForm.ACTION_DELETE, 'Delete'),
        ]
