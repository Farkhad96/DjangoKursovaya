from django.core.mail import send_mail
from django.conf import settings

from .models import Mailing, MailingAttempt


class MailingSendError(Exception):
    pass


def send_mailing(mailing: Mailing) -> tuple[int, int]:
    """Отправляет рассылку всем получателям. Возвращает (успешно, неуспешно)."""
    if not mailing.can_send():
        raise MailingSendError(
            "Отправка разрешена только в период между датой начала и датой окончания рассылки."
        )

    recipients = list(mailing.recipients.all())
    if not recipients:
        raise MailingSendError("У рассылки нет получателей.")

    attempts = []
    success_count = 0
    failure_count = 0

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts.append(
                MailingAttempt(
                    mailing=mailing,
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response="Письмо успешно отправлено.",
                )
            )
            success_count += 1
        except Exception as exc:
            attempts.append(
                MailingAttempt(
                    mailing=mailing,
                    status=MailingAttempt.STATUS_FAILURE,
                    server_response=str(exc),
                )
            )
            failure_count += 1

    if attempts:
        MailingAttempt.objects.bulk_create(attempts)

    return success_count, failure_count
