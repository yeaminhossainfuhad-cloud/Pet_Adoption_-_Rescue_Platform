from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .filters import apply_pet_filters
from .forms import AdoptionRequestForm, PetFilterForm
from .models import AdoptionRequest, Favorite, Pet


def _favorite_ids(user):
    if user.is_authenticated:
        return set(user.favorites.values_list("pet_id", flat=True))
    return set()


def home(request):
    return render(request, "pets/home.html", {
        "latest_pets": Pet.objects.filter(status=Pet.Status.AVAILABLE)[:6],
        "available_count": Pet.objects.filter(status=Pet.Status.AVAILABLE).count(),
        "adopted_count": Pet.objects.filter(status=Pet.Status.ADOPTED).count(),
        "favorite_ids": _favorite_ids(request.user),
        "filter_form": PetFilterForm(),
    })


def pet_list(request):
    form = PetFilterForm(request.GET or None)
    pets = Pet.objects.all()
    if form.is_valid():
        pets = apply_pet_filters(pets, form.cleaned_data)
    page_obj = Paginator(pets, 9).get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "pets/pet_list.html", {
        "form": form,
        "page_obj": page_obj,
        "querystring": params.urlencode(),
        "favorite_ids": _favorite_ids(request.user),
    })


def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    existing_request = None
    if request.user.is_authenticated:
        existing_request = AdoptionRequest.objects.filter(
            user=request.user, pet=pet,
            status__in=AdoptionRequest.ACTIVE_STATUSES,
        ).first()
    return render(request, "pets/pet_detail.html", {
        "pet": pet,
        "existing_request": existing_request,
        "is_favorite": pet.pk in _favorite_ids(request.user),
    })


@login_required
def adopt(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    if not pet.is_available:
        messages.error(request, f"{pet.name} has already been adopted.")
        return redirect("pet_detail", pk=pet.pk)
    if AdoptionRequest.objects.filter(
        user=request.user, pet=pet, status__in=AdoptionRequest.ACTIVE_STATUSES
    ).exists():
        messages.warning(request, f"You already have an active request for {pet.name}.")
        return redirect("my_requests")

    form = AdoptionRequestForm(request.POST or None, user=request.user, pet=pet)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except IntegrityError:
            messages.warning(request, f"You already have an active request for {pet.name}.")
            return redirect("my_requests")
        messages.success(request, f"Your application for {pet.name} was submitted.")
        return redirect("my_requests")
    return render(request, "pets/adopt.html", {"pet": pet, "form": form})


@login_required
def my_requests(request):
    requests_qs = request.user.adoption_requests.select_related("pet")
    return render(request, "pets/my_requests.html", {"adoption_requests": requests_qs})


@login_required
def favorites(request):
    favs = request.user.favorites.select_related("pet")
    return render(request, "pets/favorites.html", {
        "pets": [f.pet for f in favs],
        "favorite_ids": _favorite_ids(request.user),
    })


@login_required
@require_POST
def toggle_favorite(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, pet=pet)
    if created:
        messages.success(request, f"{pet.name} was added to your favorites.")
    else:
        favorite.delete()
        messages.info(request, f"{pet.name} was removed from your favorites.")
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return redirect(next_url)
    return redirect("pet_detail", pk=pet.pk)


@login_required
def profile(request):
    counts = {s: request.user.adoption_requests.filter(status=s).count()
              for s in AdoptionRequest.Status.values}
    return render(request, "accounts/profile.html", {
        "counts": counts,
        "favorite_count": request.user.favorites.count(),
    })
