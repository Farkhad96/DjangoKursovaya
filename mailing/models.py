from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-id"]

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_CREATED = "Создана"
    STATUS_STARTED = "Запущена"
    STATUS_COMPLETED = "Завершена"

    start_time = models.DateTimeField(verbose_name="Дата и время начала отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(
        Recipient,
        related_name="mailings",
        verbose_name="Получатели",
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_time"]

    def __str__(self):
        return f"Рассылка #{self.pk} — {self.message.subject}"

    def clean(self):
        errors = {}
        now = timezone.now()
        if not self.pk and self.start_time and self.start_time < now:
            errors["start_time"] = "Дата начала не может быть в прошлом."
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["end_time"] = "Дата окончания должна быть позже даты начала."
        if errors:
            raise ValidationError(errors)

    @property
    def status(self):
        now = timezone.now()
        if now < self.start_time:
            return self.STATUS_CREATED
        if self.start_time <= now <= self.end_time:
            return self.STATUS_STARTED
        return self.STATUS_COMPLETED

    def can_send(self):
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time


class MailingAttempt(models.Model):
    STATUS_SUCCESS = "Успешно"
    STATUS_FAILURE = "Не успешно"

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, verbose_name="Статус")
    server_response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ["-attempt_time"]

    def __str__(self):
        return f"{self.mailing_id} — {self.status} ({self.attempt_time})"
