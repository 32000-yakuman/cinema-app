# 0006_alter_reservation_checkin_token.py
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0005_populate_checkin_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='checkin_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='チェックイン用トークン'),
        ),
    ]