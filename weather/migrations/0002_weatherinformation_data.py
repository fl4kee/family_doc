# Generated by Django 4.0.2 on 2022-02-08 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies: list = [
        ("weather", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="weatherinformation",
            name="data",
            field=models.JSONField(default=None),
        ),
    ]
