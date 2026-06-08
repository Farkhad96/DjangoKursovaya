from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache_utils import invalidate_home_cache, invalidate_user_stats_cache
from .models import Mailing, MailingAttempt, Recipient


@receiver(post_save, sender=Mailing)
@receiver(post_delete, sender=Mailing)
@receiver(post_save, sender=Recipient)
@receiver(post_delete, sender=Recipient)
@receiver(post_save, sender=MailingAttempt)
def clear_caches_on_change(sender, instance, **kwargs):
    invalidate_home_cache()
    owner_id = getattr(instance, "owner_id", None)
    if owner_id is None and hasattr(instance, "mailing"):
        owner_id = instance.mailing.owner_id
    if owner_id:
        invalidate_user_stats_cache(owner_id)
