from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied


def is_manager(user) -> bool:
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=settings.MANAGER_GROUP_NAME).exists()


def get_recipient_queryset(user):
    from .models import Recipient

    if is_manager(user):
        return Recipient.objects.all()
    return Recipient.objects.filter(owner=user)


def get_message_queryset(user):
    from .models import Message

    if is_manager(user):
        return Message.objects.all()
    return Message.objects.filter(owner=user)


def get_mailing_queryset(user):
    from .models import Mailing

    if is_manager(user):
        return Mailing.objects.all()
    return Mailing.objects.filter(owner=user)


def check_owner_or_manager_view(user, obj):
    if is_manager(user):
        return
    if obj.owner != user:
        raise PermissionDenied


def check_owner_edit(user, obj):
    if obj.owner != user:
        raise PermissionDenied
