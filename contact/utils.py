from django.conf import settings


def get_language(request) -> str:
    lang = request.GET.get('lang')
    if lang:
        request.session['lang'] = lang
        return lang
    session_lang = request.session.get('lang')
    if session_lang:
        return session_lang
    return settings.DEFAULT_LANGUAGE
