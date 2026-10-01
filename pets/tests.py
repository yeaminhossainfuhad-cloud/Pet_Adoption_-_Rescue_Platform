from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import AdoptionRequest, Pet

APPLICATION = {
    "address": "House 1, Road 2, Dhaka",
    "phone": "+8801712345678",
    "reason": "I have a big garden and lots of love.",
    "previous_pet_experience": "True",
    "message": "",
}


def make_pet(**kwargs):
    data = dict(name="Max", animal_type="Dog", breed="Golden Retriever", age=2,
                gender="Male", location="Dhaka", description="Friendly.")
    data.update(kwargs)
    return Pet.objects.create(**data)


class BusinessRuleTests(TestCase):
    def setUp(self):
        self.rahim = User.objects.create_user("rahim", password="pw12345!x")
        self.karim = User.objects.create_user("karim", password="pw12345!x")
        self.pet = make_pet()

    def apply(self, user, pet=None):
        self.client.force_login(user)
        pet = pet or self.pet
        return self.client.post(reverse("adopt", args=[pet.pk]), APPLICATION)

    def test_available_pet_can_be_applied_for(self):
        self.apply(self.rahim)
        self.assertEqual(AdoptionRequest.objects.filter(user=self.rahim).count(), 1)

    def test_rule1_adopted_pet_rejects_applications(self):
        self.pet.status = Pet.Status.ADOPTED
        self.pet.save()
        self.apply(self.rahim)
        self.assertEqual(AdoptionRequest.objects.count(), 0)

    def test_rule2_no_duplicate_active_request(self):
        self.apply(self.rahim)
        self.apply(self.rahim)
        self.assertEqual(AdoptionRequest.objects.filter(user=self.rahim).count(), 1)

    def test_rejected_user_can_apply_again(self):
        self.apply(self.rahim)
        AdoptionRequest.objects.update(status="Rejected")
        self.apply(self.rahim)
        self.assertEqual(AdoptionRequest.objects.filter(user=self.rahim).count(), 2)

    def test_rule3_approval_adopts_pet_and_closes_others(self):
        self.apply(self.rahim)
        self.apply(self.karim)
        first = AdoptionRequest.objects.get(user=self.rahim)
        first.status = AdoptionRequest.Status.APPROVED
        first.save()
        self.pet.refresh_from_db()
        self.assertEqual(self.pet.status, Pet.Status.ADOPTED)
        other = AdoptionRequest.objects.get(user=self.karim)
        self.assertEqual(other.status, AdoptionRequest.Status.REJECTED)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("adopt", args=[self.pet.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_detail_page_hides_apply_button_when_adopted(self):
        self.pet.status = Pet.Status.ADOPTED
        self.pet.save()
        response = self.client.get(reverse("pet_detail", args=[self.pet.pk]))
        self.assertContains(response, "already been adopted")
        self.assertNotContains(response, "Apply for adoption")


class SearchTests(TestCase):
    def setUp(self):
        make_pet()
        make_pet(name="Luna", animal_type="Cat", breed="Persian", gender="Female", location="Sylhet")

    def test_web_filter(self):
        response = self.client.get(reverse("pet_list"), {"animal_type": "Dog", "gender": "Male", "location": "Dhaka"})
        self.assertContains(response, "Max")
        self.assertNotContains(response, "Luna")

    def test_api_filter_and_search(self):
        client = APIClient()
        data = client.get("/api/pets/", {"animal_type": "Cat"}).json()
        self.assertEqual([p["name"] for p in data["results"]], ["Luna"])
        data = client.get("/api/pets/", {"search": "golden"}).json()
        self.assertEqual([p["name"] for p in data["results"]], ["Max"])


class ApiTests(TestCase):
    def setUp(self):
        self.pet = make_pet()
        self.rahim = User.objects.create_user("rahim", password="pw12345!x")
        self.karim = User.objects.create_user("karim", password="pw12345!x")
        self.staff = User.objects.create_user("boss", password="pw12345!x", is_staff=True)
        self.client = APIClient()

    payload = {
        "address": "Dhaka", "phone": "+8801712345678",
        "reason": "Love pets", "previous_pet_experience": True,
    }

    def test_only_staff_can_create_pets(self):
        body = {"name": "Zed", "animal_type": "Dog", "gender": "Male",
                "location": "Dhaka", "description": "x", "age": 1}
        self.client.force_authenticate(self.rahim)
        self.assertEqual(self.client.post("/api/pets/", body).status_code, 403)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post("/api/pets/", body).status_code, 201)

    def test_adoption_requires_login(self):
        self.assertEqual(self.client.get("/api/adoptions/").status_code, 401)

    def test_user_creates_request_and_cannot_self_approve(self):
        self.client.force_authenticate(self.rahim)
        response = self.client.post(
            "/api/adoptions/", {**self.payload, "pet": self.pet.pk, "status": "Approved"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "Pending")

    def test_duplicate_and_adopted_requests_are_rejected(self):
        self.client.force_authenticate(self.rahim)
        body = {**self.payload, "pet": self.pet.pk}
        self.assertEqual(self.client.post("/api/adoptions/", body, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/adoptions/", body, format="json").status_code, 400)
        self.pet.status = Pet.Status.ADOPTED
        self.pet.save()
        self.client.force_authenticate(self.karim)
        self.assertEqual(self.client.post("/api/adoptions/", body, format="json").status_code, 400)

    def test_users_only_see_their_own_requests(self):
        self.client.force_authenticate(self.rahim)
        created = self.client.post("/api/adoptions/", {**self.payload, "pet": self.pet.pk}, format="json").json()
        self.client.force_authenticate(self.karim)
        self.assertEqual(self.client.get("/api/adoptions/").json()["count"], 0)
        self.assertEqual(self.client.get(f"/api/adoptions/{created['id']}/").status_code, 404)

    def test_token_auth(self):
        response = APIClient().post("/api/auth/token/", {"username": "rahim", "password": "pw12345!x"})
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        authed = APIClient()
        authed.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(authed.get("/api/adoptions/").status_code, 200)
