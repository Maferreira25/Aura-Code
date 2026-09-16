VALID={"tok-secret-alice":"alice"}

def authenticate(token, logger):
    logger.info("authentication token=%s", token)
    if token not in VALID:
        logger.warning("invalid token=%s", token)
        raise PermissionError("invalid")
    return VALID[token]
