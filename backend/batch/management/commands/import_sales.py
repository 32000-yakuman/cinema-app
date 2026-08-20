import pandas
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.storage import default_storage

from api.inventory.models import Sales, SalesFile, Status

def execute(download_history):
    with transaction.atomic():
        entry = SalesFile.objects.select_for_update().get(pk=download_history.id)
        if entry.status != Status.ASYNC_UNPROCESSED:
            return 
        
        filename = entry.file_name

        df = pandas.read_csv(default_storage.path(filename))
        for _, row in df.iterrows():
            sales = Sales(
                product_id=row['product'],
                sales_date=row['date'],
                quantity=row['quantity'],
                import_file=entry
            )
            sales.save()

        entry.status = Status.ASYNC_PROCESSED
        entry.save()

# djangoのカスタムコマンド
class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            download_history = SalesFile.objects.filter(
                status=Status.ASYNC_UNPROCESSED).order_by('id').first()
            
            if download_history is None:
                break
            else:
                execute(download_history)