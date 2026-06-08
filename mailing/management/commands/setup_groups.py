from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from django.conf import settings


class Command(BaseCommand):
    help = "Создаёт группу менеджеров"

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=settings.MANAGER_GROUP_NAME)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Группа "{settings.MANAGER_GROUP_NAME}" создана.'))
        else:
            self.stdout.write(f'Группа "{settings.MANAGER_GROUP_NAME}" уже существует.')
