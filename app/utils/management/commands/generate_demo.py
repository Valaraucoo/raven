from django.conf import settings
from django.core.management import base, call_command

from utils.demo import demos_registry


class Command(base.BaseCommand):
    help = 'Generates demo for developers'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise EnvironmentError('Allowed only in development!')
        call_command('flush', '--noinput')
        self.generate_demos()

    def generate_demos(self):
        for demo in demos_registry.DEMOS:
            demo.generate()
            self.stdout.write(self.style.SUCCESS(demo.INFO))
