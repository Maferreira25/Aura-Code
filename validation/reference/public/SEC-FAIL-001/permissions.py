def may_delete(user_id, policy_client):
    try:
        return policy_client.allowed(user_id, "delete") is True
    except Exception:
        return False
