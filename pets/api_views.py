from rest_framework import filters, viewsets
from rest_framework.exceptions import PermissionDenied

from .filters import apply_pet_filters
from .models import AdoptionRequest, Pet
from .permissions import IsStaffOrReadOnly
from .serializers import AdoptionRequestSerializer, PetSerializer


class PetViewSet(viewsets.ModelViewSet):
    """
    list / retrieve are public. create / update / delete require a staff user.

    ?search=golden               text search (name, breed, type, location, description)
    ?animal_type=Dog             ?gender=Male   ?location=Dhaka
    ?breed=retriever             ?status=Available   ?page=2
    """

    serializer_class = PetSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "breed", "animal_type", "location", "description"]
    ordering_fields = ["created_at", "age", "name"]

    def get_queryset(self):
        return apply_pet_filters(Pet.objects.all(), self.request.query_params)


class AdoptionRequestViewSet(viewsets.ModelViewSet):
    """Users see and manage only their own requests; staff can see all."""

    serializer_class = AdoptionRequestSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        qs = AdoptionRequest.objects.select_related("user", "pet")
        user = self.request.user
        return qs if user.is_staff else qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_staff and serializer.instance.status != AdoptionRequest.Status.PENDING:
            raise PermissionDenied("Only pending requests can be edited.")
        serializer.save()
