from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import Mailing, MailingAttempt, Recipient


def _home_cache_key(user_id):
    return f"home_stats_{user_id or 'anon'}"


def get_home_statistics(user):
    key = _home_cache_key(user.id if user.is_authenticated else None)
    stats = cache.get(key)
    if stats is not None:
        return stats

    now = timezone.now()
    mailings_qs = Mailing.objects.all()
    if user.is_authenticated and not user.groups.filter(name=settings.MANAGER_GROUP_NAME).exists():
        mailings_qs = mailings_qs.filter(owner=user)

    total_mailings = mailings_qs.count()
    active_mailings = sum(
        1
        for m in mailings_qs.filter(start_time__lte=now, end_time__gte=now, is_active=True)
        if m.status == Mailing.STATUS_STARTED
    )

    if user.is_authenticated and not user.groups.filter(name=settings.MANAGER_GROUP_NAME).exists():
        unique_recipients = Recipient.objects.filter(owner=user).count()
    else:
        unique_recipients = Recipient.objects.count()

    stats = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_recipients": unique_recipients,
    }
    cache.set(key, stats, settings.CACHE_TTL)
    return stats


def _stats_cache_key(user_id):
    return f"user_stats_{user_id}"


def get_user_statistics(user):
    key = _stats_cache_key(user.id)
    stats = cache.get(key)
    if stats is not None:
        return stats

    mailings = Mailing.objects.filter(owner=user)
    attempts = MailingAttempt.objects.filter(mailing__owner=user)
    stats = {
        "total_mailings": mailings.count(),
        "success_attempts": attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count(),
        "failure_attempts": attempts.filter(status=MailingAttempt.STATUS_FAILURE).count(),
        "total_sent": attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count(),
    }
    cache.set(key, stats, settings.CACHE_TTL)
    return stats


def invalidate_home_cache():
    cache.delete_many([_home_cache_key(None)])
    from django.contrib.auth import get_user_model

    User = get_user_model()
    keys = [_home_cache_key(uid) for uid in User.objects.values_list("id", flat=True)]
    cache.delete_many(keys)


def invalidate_user_stats_cache(user_id):
    cache.delete(_stats_cache_key(user_id))
