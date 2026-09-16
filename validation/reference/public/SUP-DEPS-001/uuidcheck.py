from uuid import UUID

def is_valid_uuid(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return len(value) == 36 and str(parsed) == value.lower()
