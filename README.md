# Homeward: Pet Adoption & Rescue Platform

A Django web app where people browse pets, apply to adopt, and track their requests.
Admins manage everything from Django Admin. A Django REST Framework API exposes the same data.

## Features

**Website (Django templates + Bootstrap 5)**
- Register, login, logout, profile page
- Pet list with cards, search/filter (name, type, breed, gender, location, status) and pagination
- Pet detail page; the Apply button disappears when a pet is adopted
- Adoption form, and a dashboard of the user's requests (Pending / Approved / Rejected)
- Success and error messages, responsive layout, favorites (bonus)

**Admin**
- Add, edit, delete pets, upload images, change adoption status
- Review adoption requests (user, pet, date, phone, reason, status) and approve or reject them,
  from the detail page or with bulk actions

**REST API (DRF)**: see the endpoint table below. Includes search, filtering, pagination and token authentication.

## Business rules

| Rule | Where it is enforced |
|------|----------------------|
| 1. Only available pets can be adopted | `AdoptionRequest.clean()`; used by the form, admin and API |
| 2. One active (pending/approved) request per user per pet | `AdoptionRequest.clean()` plus a conditional `UniqueConstraint` in the database |
| 3. Approving a request marks the pet Adopted | `AdoptionRequest.save()`; other pending requests for that pet are set to Rejected, and new applications are blocked by rule 1 |

A user whose request was rejected may apply again.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo         # optional: 12 demo pets and a user (rahim / demo-pass-123)
python manage.py runserver
```

- Website: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- API root: http://127.0.0.1:8000/api/

Run the tests with `python manage.py test`.

If Django reports model changes after an upgrade, run `python manage.py makemigrations` and commit the result.

## API

| Method | Endpoint | Who |
|--------|----------|-----|
| GET | `/api/pets/` | anyone |
| GET | `/api/pets/<id>/` | anyone |
| POST, PUT, PATCH, DELETE | `/api/pets/`, `/api/pets/<id>/` | staff only |
| GET, POST | `/api/adoptions/` | logged-in user (own requests; staff see all) |
| GET, PUT, PATCH | `/api/adoptions/<id>/` | owner while Pending; staff can also change status |
| POST | `/api/auth/token/` | get a token with `username` and `password` |

Search, filters and pagination on `/api/pets/`:

```
/api/pets/?search=golden
/api/pets/?animal_type=Dog&gender=Male
/api/pets/?location=Dhaka&status=Available
/api/pets/?ordering=-age&page=2
```

Example with token authentication:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ -d "username=rahim&password=demo-pass-123"
# {"token": "abc123..."}

curl -X POST http://127.0.0.1:8000/api/adoptions/ \
  -H "Authorization: Token abc123..." -H "Content-Type: application/json" \
  -d '{"pet": 1, "phone": "+8801712345678", "address": "Dhaka",
       "reason": "I have a garden", "previous_pet_experience": true}'
```

## Project layout

```
config/     settings, root URLs
accounts/   register / login / logout views and forms
pets/       models, admin, website views, forms, serializers, API views, tests
templates/  base layout, includes, page templates
static/     css/style.css
```

## Models

- **Pet**: name, animal_type (Dog, Cat, Bird, Rabbit, Other), breed, age, gender, location, description, image, status, created_at
- **AdoptionRequest**: user, pet, phone, address, reason, previous_pet_experience, message, status, created_at
- **Favorite** (bonus): user, pet

Uses Django's built-in `User` model.
