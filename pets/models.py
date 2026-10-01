from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from .validators import validate_phone


class Pet(models.Model):
    class AnimalType(models.TextChoices):
        DOG = "Dog", "Dog"
        CAT = "Cat", "Cat"
        BIRD = "Bird", "Bird"
        RABBIT = "Rabbit", "Rabbit"
        OTHER = "Other", "Other"

    class Gender(models.TextChoices):
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"

    class Status(models.TextChoices):
        AVAILABLE = "Available", "Available"
        ADOPTED = "Adopted", "Adopted"

    name = models.CharField(max_length=100)
    animal_type = models.CharField(
        max_length=20, choices=AnimalType.choices, default=AnimalType.DOG
    )
    breed = models.CharField(max_length=100, blank=True)
    age = models.PositiveSmallIntegerField(
        default=0, help_text="Age in years. Use 0 for under a year."
    )
    gender = models.CharField(max_length=10, choices=Gender.choices)
    location = models.CharField(max_length=120)
    description = models.TextField()
    image = models.ImageField(upload_to="pets/%Y/%m/", blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.name} ({self.animal_type})"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def age_display(self):
        if self.age == 0:
            return "Under 1 year"
        return f"{self.age} year" + ("" if self.age == 1 else "s")

    @property
    def emoji(self):
        return {
            "Dog": "🐕",
            "Cat": "🐈",
            "Bird": "🐦",
            "Rabbit": "🐇",
        }.get(self.animal_type, "🐾")


class AdoptionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"

    ACTIVE_STATUSES = (Status.PENDING, Status.APPROVED)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adoption_requests",
    )
    pet = models.ForeignKey(
        Pet, on_delete=models.CASCADE, related_name="adoption_requests"
    )
    phone = models.CharField(max_length=20, validators=[validate_phone])
    address = models.CharField(max_length=255)
    reason = models.TextField(verbose_name="Reason for adoption")
    previous_pet_experience = models.BooleanField(
        default=False, verbose_name="Has owned a pet before"
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            # Rule 2 at the database level: one active (pending/approved)
            # request per user per pet.
            models.UniqueConstraint(
                fields=["user", "pet"],
                condition=models.Q(status__in=["Pending", "Approved"]),
                name="unique_active_request_per_user_pet",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.pet.name} ({self.status})"

    @property
    def badge_class(self):
        return {
            self.Status.PENDING: "text-bg-warning",
            self.Status.APPROVED: "text-bg-success",
            self.Status.REJECTED: "text-bg-secondary",
        }[self.status]

    def clean(self):
        """Business rules 1-3, shared by forms, admin and the API."""
        if self.pet_id is None:
            return
        pet = self.pet

        # Rule 1: only available pets can receive new applications.
        if self._state.adding and not pet.is_available:
            raise ValidationError("This pet has already been adopted.")

        # Rule 2: no second active request from the same user for the same pet.
        if self.user_id and self.status in self.ACTIVE_STATUSES:
            duplicate = AdoptionRequest.objects.filter(
                user_id=self.user_id,
                pet_id=self.pet_id,
                status__in=self.ACTIVE_STATUSES,
            ).exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError(
                    "You already have an active adoption request for this pet."
                )

        # Rule 3: a request cannot be approved once the pet is adopted.
        if self.status == self.Status.APPROVED and not pet.is_available:
            already_approved = (
                self.pk
                and AdoptionRequest.objects.filter(
                    pk=self.pk, status=self.Status.APPROVED
                ).exists()
            )
            if not already_approved:
                raise ValidationError(
                    "This pet has already been adopted, so this request "
                    "cannot be approved."
                )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.status == self.Status.APPROVED:
                # Rule 3: approval marks the pet adopted and closes the
                # remaining pending requests for that pet.
                if self.pet.status != Pet.Status.ADOPTED:
                    self.pet.status = Pet.Status.ADOPTED
                    self.pet.save(update_fields=["status"])
                AdoptionRequest.objects.filter(
                    pet=self.pet, status=self.Status.PENDING
                ).exclude(pk=self.pk).update(status=self.Status.REJECTED)


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "pet"], name="unique_favorite")
        ]

    def __str__(self):
        return f"{self.user} likes {self.pet.name}"
