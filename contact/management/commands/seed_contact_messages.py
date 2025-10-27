# contact/management/commands/seed_contact_messages.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from contact.models import ContactMessage

try:
    from faker import Faker
except Exception:
    Faker = None


def has_field(model, name):
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False


def get_status_choices(model):
    """
    Возвращает список допустимых значений статуса, если поле и choices существуют.
    Иначе — разумный дефолт или None.
    """
    if not has_field(model, "status"):
        return None
    try:
        field = model._meta.get_field("status")
        if getattr(field, "choices", None):
            return [c[0] for c in field.choices]
    except Exception:
        pass
    # если choices нет — подставим базовый набор
    return ["new", "in_progress", "done"]


class Command(BaseCommand):
    help = "Seed ContactMessage with fake data."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=1000, help="Сколько записей создать")
        parser.add_argument("--chunk", type=int, default=1000, help="Размер пачки в bulk_create")
        parser.add_argument("--locale", type=str, default="pl_PL", help="Локаль Faker (pl_PL, en_US...)")
        parser.add_argument("--status", type=str, default="", help="Принудительный статус (если поле есть)")
        parser.add_argument("--clean", action="store_true", help="Сначала очистить таблицу")

    def handle(self, *args, **opt):
        if Faker is None:
            self.stderr.write("Faker не установлен. Установи: pip install Faker")
            return

        count = opt["count"]
        chunk_size = opt["chunk"]
        fake = Faker(opt["locale"])
        forced_status = (opt["status"] or "").strip() or None
        statuses = get_status_choices(ContactMessage)

        if opt["clean"]:
            self.stdout.write("Очищаю таблицу ContactMessage…")
            ContactMessage.objects.all().delete()

        objs = []
        now = timezone.now()

        # какие поля реально есть
        has_status = has_field(ContactMessage, "status")
        has_is_deleted = has_field(ContactMessage, "is_deleted")
        has_created_at = has_field(ContactMessage, "created_at")
        has_phone = has_field(ContactMessage, "phone")
        has_company = has_field(ContactMessage, "company")

        for _ in range(count):
            data = {
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.email(),
                "message": fake.paragraph(nb_sentences=5),
            }
            if has_phone:
                # msisdn иногда длинный — ограничим
                data["phone"] = (fake.msisdn() or "")[:15]
            if has_company:
                data["company"] = fake.company()
            if has_status:
                if forced_status:
                    data["status"] = forced_status
                elif statuses:
                    data["status"] = fake.random_element(statuses)
            if has_is_deleted:
                data["is_deleted"] = False
            if has_created_at:
                data["created_at"] = now - timedelta(days=fake.random_int(min=0, max=90))

            objs.append(ContactMessage(**data))

            if len(objs) >= chunk_size:
                with transaction.atomic():
                    ContactMessage.objects.bulk_create(objs, batch_size=chunk_size)
                objs = []  # вместо clear()

        if objs:
            with transaction.atomic():
                ContactMessage.objects.bulk_create(objs, batch_size=chunk_size)

        self.stdout.write(self.style.SUCCESS("Готово: добавлено {} записей".format(count)))
