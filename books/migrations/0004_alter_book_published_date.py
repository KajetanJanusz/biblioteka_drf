# Generated by Django 5.1.3 on 2025-03-31 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_book_is_deleted_customuser_is_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='published_date',
            field=models.DateField(null=True),
        ),
    ]
