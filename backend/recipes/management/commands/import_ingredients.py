import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import ingredients from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file_path',
            type=str, help='The CSV file path'
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file_path']

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Ingredient.objects.create(
                    name=row['name'],
                    measurement_unit=row['measurement_unit'])

        self.stdout.write(
            self.style.SUCCESS('Successfully imported ingredients'))
