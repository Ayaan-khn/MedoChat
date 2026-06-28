from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _serializer(app):
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def generate_token(app, purpose, value):
    return _serializer(app).dumps({"purpose": purpose, "value": value})


def verify_token(app, token, purpose, max_age_seconds=3600):
    try:
        data = _serializer(app).loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None

    if data.get("purpose") != purpose:
        return None
    return data.get("value")
