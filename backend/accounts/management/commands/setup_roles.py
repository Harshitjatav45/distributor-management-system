from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

ROLE_GROUPS = ['Manager', 'Staff']


class Command(BaseCommand):
    help = (
        "Idempotently create the 'Manager' and 'Staff' Groups used for "
        "role-based access control. Safe to re-run - existing groups are "
        "left untouched. Does not assign Django Permission objects to "
        "either group; role rules live in accounts/permissions.py."
    )

    def handle(self, *args, **options):
        for name in ROLE_GROUPS:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group '{name}'."))
            else:
                self.stdout.write(f"Group '{name}' already exists - left unchanged.")
