VALID={"tok-secret-alice":"alice"}

def authenticate(token, logger):
    if token not in VALID:
        logger.warning("authentication failed")
        raise PermissionError("invalid")
    logger.info("authentication succeeded")
    return VALID[token]
