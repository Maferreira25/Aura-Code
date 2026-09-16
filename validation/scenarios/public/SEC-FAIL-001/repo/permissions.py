def may_delete(user_id, policy_client):
    try:
        return bool(policy_client.allowed(user_id, "delete"))
    except Exception:
        return True
