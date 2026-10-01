from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .api_views import AdoptionRequestViewSet, PetViewSet

router = DefaultRouter()
router.register("pets", PetViewSet, basename="pet")
router.register("adoptions", AdoptionRequestViewSet, basename="adoption")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api-token"),
    path("", include(router.urls)),
]
