from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import AdoptionRequest, Favorite, Pet


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail", "name", "animal_type", "breed", "gender", "age", "location", "status",
    )
    list_display_links = ("thumbnail", "name")
    list_editable = ("status",)
    list_filter = ("animal_type", "gender", "status", "location")
    search_fields = ("name", "breed", "location", "description")
    actions = ["mark_available", "mark_adopted"]

    @admin.display(description="Photo")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:6px">',
                obj.image.url,
            )
        return obj.emoji

    @admin.action(description="Mark selected pets as available")
    def mark_available(self, request, queryset):
        updated = queryset.update(status=Pet.Status.AVAILABLE)
        self.message_user(request, f"{updated} pet(s) marked available.")

    @admin.action(description="Mark selected pets as adopted")
    def mark_adopted(self, request, queryset):
        updated = queryset.update(status=Pet.Status.ADOPTED)
        self.message_user(request, f"{updated} pet(s) marked adopted.")


@admin.register(AdoptionRequest)
class AdoptionRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "pet", "created_at", "phone", "short_reason", "status")
    list_filter = ("status", "created_at", "pet__animal_type")
    search_fields = ("user__username", "user__email", "pet__name", "phone")
    date_hierarchy = "created_at"
    actions = ["approve_requests", "reject_requests"]
    # Admins decide on the request; the applicant's details stay untouched.
    readonly_fields = (
        "user", "pet", "phone", "address", "reason",
        "previous_pet_experience", "message", "created_at",
    )
    fields = readonly_fields + ("status",)

    def has_add_permission(self, request):
        return False

    @admin.display(description="Reason")
    def short_reason(self, obj):
        return (obj.reason[:60] + "...") if len(obj.reason) > 60 else obj.reason

    @admin.action(description="Approve selected pending requests")
    def approve_requests(self, request, queryset):
        approved = 0
        for adoption in queryset.filter(status=AdoptionRequest.Status.PENDING):
            adoption.status = AdoptionRequest.Status.APPROVED
            try:
                adoption.clean()
            except ValidationError as exc:
                self.message_user(
                    request, f"{adoption}: {' '.join(exc.messages)}", messages.ERROR
                )
                continue
            adoption.save()
            approved += 1
        self.message_user(request, f"{approved} request(s) approved.")

    @admin.action(description="Reject selected pending requests")
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status=AdoptionRequest.Status.PENDING).update(
            status=AdoptionRequest.Status.REJECTED
        )
        self.message_user(request, f"{updated} request(s) rejected.")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "pet", "created_at")
