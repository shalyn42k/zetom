from flask import request, session

# смена языка(думаю надо переделать)
def get_language():
    lang = request.args.get('lang', session.get('lang', 'pl'))
    session['lang'] = lang
    return lang