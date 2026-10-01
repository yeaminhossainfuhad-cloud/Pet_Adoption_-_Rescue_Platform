from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import AdoptionRequest, Pet


class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = [
            "id", "name", "animal_type", "breed", "age", "gender",
            "location", "description", "image", "status", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AdoptionRequestSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    pet_name = serializers.CharField(source="pet.name", read_only=True)

    class Meta:
        model = AdoptionRequest
        fields = [
            "id", "user", "pet", "pet_name", "phone", "address", "reason",
            "previous_pet_experience", "message", "status", "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        # Only staff may change the decision; applicants cannot approve themselves.
        if not (request and request.user and request.user.is_staff):
            fields["status"].read_only = True
        return fields

    def validate(self, attrs):
        request = self.context["request"]
        if self.instance is None:
            probe = AdoptionRequest(user=request.user, pet=attrs["pet"])
            try:
                probe.clean()
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages)
        elif "pet" in attrs and attrs["pet"] != self.instance.pet:
            raise serializers.ValidationError({"pet": "The pet cannot be changed."})
        return attrs

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        instance.save()
        return instance
