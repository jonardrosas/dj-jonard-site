from django.core.management.base import BaseCommand
from core.services.porkbun import get_ssl


class Command(BaseCommand):
    help = "Generate SSL certificates from Porkbun and save them to disk."

    def handle(self, *args, **options):
        return get_ssl()