# Generated by Django 2.2.16 on 2023-02-06 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20230125_0615'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'verbose_name': ('Группа',), 'verbose_name_plural': ('Группы',)},
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date',), 'verbose_name': ('Пост',), 'verbose_name_plural': 'Посты'},
        ),
        migrations.AlterField(
            model_name='post',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации'),
        ),
    ]
