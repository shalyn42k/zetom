from infrastructure.email_module import verify_email

def send_contact_email(to_email, message):
    subject = "Nowa wiadomość z formularza kontaktowego"
    body = f"""
    Imię i nazwisko: {message.imie} {message.nazwisko}
    Telefon: {message.telefon}
    E-mail: {message.email}
    Firma: {message.firma}
    Wiadomość: {message.tresc_wiadomosci}
    """
    verify_email(to_email, subject, body)
