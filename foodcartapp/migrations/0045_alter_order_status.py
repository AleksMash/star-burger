# Generated by Django 3.2.15 on 2023-06-08 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0044_auto_20230608_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('NEW', 'Не обработан'), ('COOK', 'Готовится'), ('DLVR', 'Доставка'), ('DONE', 'Доставлен')], db_index=True, default='NEW', max_length=4, verbose_name='Статус'),
        ),
    ]
