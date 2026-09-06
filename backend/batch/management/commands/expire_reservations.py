from django.core.management.base import BaseCommand
from django.db import transaction

from api.cinema.models import expire_pending_reservations


class Command(BaseCommand):
    help = (
        "有効期限切れのPENDING予約を"
        "キャンセルして座席を解放します"
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            count = expire_pending_reservations()

        self.stdout.write(
            self.style.SUCCESS(
                f"期限切れ予約を{count}件処理しました。"
            )
        )