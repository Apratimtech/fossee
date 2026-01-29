from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo user (admin/admin) for API authentication.'

    def handle(self, *args, **options):
        u, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@demo.local', 'is_staff': True, 'is_superuser': True},
        )
        if created:
            u.set_password('admin')
            u.save()
            self.stdout.write(self.style.SUCCESS('Demo user created: username=admin, password=admin'))
        else:
            u.set_password('admin')
            u.save()
            self.stdout.write(self.style.SUCCESS('Demo user password reset to: admin'))
