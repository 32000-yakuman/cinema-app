import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0003_remove_payment_point_payment_cannot_be_peding_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='checkin_token',
            field=models.UUIDField(null=True, editable=False, verbose_name='チェックイン用トークン'),
        ),
    ]