from common.migrate_util import common_load_fixture
from django.conf import settings
from django.core.management import call_command
from django.db import migrations

def load_fixture(apps, schema_editor):
    common_load_fixture(__file__)

class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0006_dml_insert_category_data_by_fixture"),
    ]

    operations = [
        migrations.RunPython(load_fixture)
    ]
