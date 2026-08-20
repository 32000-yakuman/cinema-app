from django.conf import settings
from django.db import migrations

def insert_category(apps, schema_editor):
    setting_file = settings.SETTINGS_MODULE
    env_name = setting_file.split('.')[-1]

    if env_name == 'development':
        Category = apps.get_model('inventory', 'Category')
        Category.objects.create(name='開発環境用のカテゴリ', parent_category=None)
    else:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_dml_insert_category_data_by_model"),
    ]

    operations = [
        migrations.RunPython(insert_category)
    ]
