from django.db import migrations
import django.db.models.fields

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0019_complaintcategory_noticecategory_and_more'),
    ]
    operations = [
        migrations.AlterField(
            model_name='publicchat',
            name='message',
            field=django.db.models.fields.TextField(blank=True, verbose_name='메시지'),
        ),
    ]
