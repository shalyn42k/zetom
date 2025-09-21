from models.contact import ContactMessage, db

def add_message(imie, nazwisko, telefon, email, firma, tresc):
    msg = ContactMessage(
        imie=imie,
        nazwisko=nazwisko,
        telefon=telefon,
        email=email,
        firma=firma,
        tresc_wiadomosci=tresc
    )
    db.session.add(msg)
    db.session.commit()
    return msg

def mark_messages_read(ids):
    ContactMessage.query.filter(ContactMessage.id.in_(ids)).update(
        {ContactMessage.is_read: True}, synchronize_session=False
    )
    db.session.commit()


def delete_messages(ids):
    ContactMessage.query.filter(ContactMessage.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()

