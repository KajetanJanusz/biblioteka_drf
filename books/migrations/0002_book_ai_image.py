# Generated by Django 5.1.3 on 2025-01-19 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="ai_image",
            field=models.ImageField(blank=True, null=True, upload_to="book_covers/"),
        ),
    ]
