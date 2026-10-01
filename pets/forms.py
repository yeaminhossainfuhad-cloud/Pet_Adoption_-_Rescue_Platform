from django import forms

from accounts.forms import BootstrapMixin

from .models import AdoptionRequest, Pet


class PetFilterForm(BootstrapMixin, forms.Form):
    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(
        attrs={"placeholder": "Name, breed or type"}))
    animal_type = forms.ChoiceField(
        required=False, label="Animal type",
        choices=[("", "Any type")] + list(Pet.AnimalType.choices),
    )
    breed = forms.CharField(required=False)
    gender = forms.ChoiceField(
        required=False, choices=[("", "Any gender")] + list(Pet.Gender.choices)
    )
    location = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False, label="Adoption status",
        choices=[("", "Any status")] + list(Pet.Status.choices),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_widgets()


class AdoptionRequestForm(BootstrapMixin, forms.ModelForm):
    previous_pet_experience = forms.TypedChoiceField(
        label="Have you owned a pet before?",
        choices=[("True", "Yes"), ("False", "No")],
        coerce=lambda value: value == "True",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = AdoptionRequest
        fields = ["address", "phone", "reason", "previous_pet_experience", "message"]
        labels = {
            "reason": "Why do you want this pet?",
            "message": "Additional message (optional)",
        }
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 4}),
            "message": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user, pet, **kwargs):
        super().__init__(*args, **kwargs)
        # Set before validation so AdoptionRequest.clean() can enforce the
        # business rules (available pet, no duplicate active request).
        self.instance.user = user
        self.instance.pet = pet
        self._style_widgets()
