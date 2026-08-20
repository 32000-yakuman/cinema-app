from django.db import migrations

def insert_category(apps, schema_editor):
    Category = apps.get_model('inventory', 'category')
    Category.objects.create(name='レディース', parent_category=None)

class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0003_dml_insert_category_data"),
    ]

    operations = [
        migrations.RunPython(insert_category)
    ]