def is_valid_uuid(value):
    return isinstance(value, str) and len(value) == 36 and value.count("-") == 4
