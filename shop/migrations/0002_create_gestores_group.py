from django.db import migrations


def create_gestores_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.using(schema_editor.connection.alias).get_or_create(name="gestores")


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("shop", "0001_initial_domain"),
    ]

    operations = [migrations.RunPython(create_gestores_group, migrations.RunPython.noop)]
