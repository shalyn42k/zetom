from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.contact_services import delete_messages, mark_messages_read
from models.contact import ContactMessage
from config import Config
from services.language_services import get_language
from services.contact_services import add_message
from services.email_services import  send_contact_email
from infrastructure.email_module import send_email_with_attachment

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    lang = get_language()
    if request.method == 'POST':
        password = request.form.get('password')

        if not password:
            flash("Hasło jest wymagane!" if lang == "pl" else "Password is required!")
        elif password == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('routes.panel'))
        else:
            flash("Nieprawidłowe hasło!" if lang == "pl" else "Wrong password!")

    return render_template('admin_login.html', lang=lang)


@bp.route('/panel', methods=["GET", "POST"])
def panel():
    # простая проверка авторизации
    if 'logged_in' not in session:
        return redirect(url_for('routes.login'))

    lang = get_language()

    if request.method == "POST":
        action = request.form.get("action")
        selected_ids = list(map(int, request.form.getlist("selected")))
        if action == "mark_read":
            mark_messages_read(selected_ids)
        elif action == "delete":
            delete_messages(selected_ids)
        return redirect(url_for('routes.panel'))

    # GET — показываем все записи из базы
    inquiries = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin_panel.html", lang=lang, inquiries=inquiries)


@bp.route("/submit", methods=["POST"])
def submit():
    user_email = request.form.get("email")

    imie = request.form.get("imie")
    nazwisko = request.form.get("nazwisko")
    telefon = request.form.get("telefon")
    firma = request.form.get("firma")
    tresc = request.form.get("tresc_wiadomosci")

    msg = add_message(imie, nazwisko, telefon, user_email, firma, tresc)

    send_contact_email(user_email, msg)

    return redirect(url_for("routes.index"))

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('routes.index'))

@bp.route("/send-email", methods=["POST"])
def sent_email():
    to_email = request.form.get("to_email")
    body = request.form.get("body")
    file = request.files.get("attachment")
    return redirect(url_for("routes.panel"))
