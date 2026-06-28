import re

USERNAME_PATTERN = re.compile(r"[^a-z0-9_]")


def normalize_username(value):
    return USERNAME_PATTERN.sub("", value.strip().lower())


def normalize_email(value):
    return value.strip().lower()


def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must include a lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must include a number.")
    return errors
