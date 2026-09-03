# 0005_populate_checkin_token.py
import uuid
from django.db import migrations


def populate_checkin_token(apps, schema_editor):
    Reservation = apps.get_model('cinema', 'Reservation')
    for reservation in Reservation.objects.all():
        reservation.checkin_token = uuid.uuid4()
        reservation.save(update_fields=['checkin_token'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0004_reservation_checkin_token'),
    ]

    operations = [
        migrations.RunPython(populate_checkin_token, reverse_noop),
    ]