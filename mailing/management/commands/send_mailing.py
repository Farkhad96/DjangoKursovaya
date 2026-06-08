from django.core.management.base import BaseCommand, CommandError

from mailing.models import Mailing
from mailing.services import MailingSendError, send_mailing


class Command(BaseCommand):
    help = "Отправляет рассылку по ID"

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int, help="ID рассылки")

    def handle(self, *args, **options):
        mailing_id = options["mailing_id"]
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist as exc:
            raise CommandError(f"Рассылка с ID {mailing_id} не найдена.") from exc

        try:
            success, failure = send_mailing(mailing)
        except MailingSendError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Рассылка #{mailing_id} отправлена. Успешно: {success}, неуспешно: {failure}."
            )
        )
