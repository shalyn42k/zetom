from extensions import db
from datetime import datetime


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    imie = db.Column(db.String(100), nullable=False)
    nazwisko = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    firma = db.Column(db.String(50), nullable=False)  # firma1 / firma2 / firma3 / inna
    tresc_wiadomosci = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<ContactMessage {self.id} {self.email}>"
