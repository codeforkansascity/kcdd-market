# Generated migration for donor profile enhancements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donorprofile',
            name='display_name',
            field=models.CharField(default='Anonymous Donor', help_text='Public display name', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='donorprofile',
            name='bio',
            field=models.TextField(blank=True, help_text='Brief bio or description'),
        ),
        migrations.AddField(
            model_name='donorprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, help_text='Profile picture', null=True, upload_to='donor_profiles/'),
        ),
    ]
