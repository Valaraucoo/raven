from django.conf import settings
from django.core.management import base
from django.core.management import call_command

from demo import demos_registry


class Command(base.BaseCommand):
    help = 'Generates demo for developers'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise EnvironmentError('Allowed only in development!')
        self.clean_database()
        self.generate_demos()

    def clean_database(self):
        call_command('flush', '--noinput')

    def generate_demos(self):
        for demo in demos_registry.DEMOS:
            demo.generate()
            for info in demo.get_info():
                self.stdout.write(self.style.SUCCESS(info))
