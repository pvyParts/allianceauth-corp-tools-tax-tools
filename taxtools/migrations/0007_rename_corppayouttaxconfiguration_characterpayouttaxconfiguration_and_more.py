# Generated by Django 4.0.7 on 2022-10-04 07:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corptools', '0077_fullyloadedfilter_reversed_logic'),
        ('taxtools', '0006_alter_corptaxhistory_unique_together'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CorpPayoutTaxConfiguration',
            new_name='CharacterPayoutTaxConfiguration',
        ),
        migrations.RenameModel(
            old_name='CorpPayoutTaxRecord',
            new_name='CharacterPayoutTaxRecord',
        ),
    ]
