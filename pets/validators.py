import re

from django.core.exceptions import ValidationError

_PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-]{6,19}$")


def validate_phone(value):
    if not _PHONE_RE.match(value or ""):
        raise ValidationError("Enter a valid phone number, e.g. +880 1712-345678.")
