import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import pets.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Pet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("animal_type", models.CharField(choices=[("Dog", "Dog"), ("Cat", "Cat"), ("Bird", "Bird"), ("Rabbit", "Rabbit"), ("Other", "Other")], default="Dog", max_length=20)),
                ("breed", models.CharField(blank=True, max_length=100)),
                ("age", models.PositiveSmallIntegerField(default=0, help_text="Age in years. Use 0 for under a year.")),
                ("gender", models.CharField(choices=[("Male", "Male"), ("Female", "Female")], max_length=10)),
                ("location", models.CharField(max_length=120)),
                ("description", models.TextField()),
                ("image", models.ImageField(blank=True, upload_to="pets/%Y/%m/")),
                ("status", models.CharField(choices=[("Available", "Available"), ("Adopted", "Adopted")], default="Available", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="AdoptionRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(max_length=20, validators=[pets.validators.validate_phone])),
                ("address", models.CharField(max_length=255)),
                ("reason", models.TextField(verbose_name="Reason for adoption")),
                ("previous_pet_experience", models.BooleanField(default=False, verbose_name="Has owned a pet before")),
                ("message", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")], default="Pending", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("pet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="adoption_requests", to="pets.pet")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="adoption_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="Favorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("pet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorited_by", to="pets.pet")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddConstraint(
            model_name="adoptionrequest",
            constraint=models.UniqueConstraint(condition=models.Q(("status__in", ["Pending", "Approved"])), fields=("user", "pet"), name="unique_active_request_per_user_pet"),
        ),
        migrations.AddConstraint(
            model_name="favorite",
            constraint=models.UniqueConstraint(fields=("user", "pet"), name="unique_favorite"),
        ),
    ]
