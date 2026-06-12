def validate(input_data, schema):
    """Simple validator that enforces presence of required fields.

    Raises ValueError when required fields are missing.
    """
    if not schema:
        return True

    required = schema.get("required", [])
    missing = [f for f in required if f not in (input_data or {})]
    if missing:
        raise ValueError("Missing required fields: %s" % ", ".join(missing))

    return True