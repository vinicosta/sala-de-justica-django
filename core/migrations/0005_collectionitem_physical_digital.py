from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_issue_synopsis'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collectionitem',
            name='is_digital',
        ),
        migrations.AddField(
            model_name='collectionitem',
            name='has_physical',
            field=models.BooleanField(
                default=False,
                help_text='Possui a versão física',
            ),
        ),
        migrations.AddField(
            model_name='collectionitem',
            name='has_digital',
            field=models.BooleanField(
                default=False,
                help_text='Possui a versão digital',
            ),
        ),
    ]
