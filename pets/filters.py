from django.db.models import Q


def apply_pet_filters(queryset, params):
    """Filter a Pet queryset from a dict-like of parameters.

    Shared by the website search form and the REST API so both behave the same.
    """
    get = params.get

    q = (get("q") or "").strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) | Q(breed__icontains=q) | Q(animal_type__icontains=q)
        )
    if get("name"):
        queryset = queryset.filter(name__icontains=get("name").strip())
    if get("animal_type"):
        queryset = queryset.filter(animal_type__iexact=get("animal_type").strip())
    if get("breed"):
        queryset = queryset.filter(breed__icontains=get("breed").strip())
    if get("gender"):
        queryset = queryset.filter(gender__iexact=get("gender").strip())
    if get("location"):
        queryset = queryset.filter(location__icontains=get("location").strip())
    if get("status"):
        queryset = queryset.filter(status__iexact=get("status").strip())
    return queryset
