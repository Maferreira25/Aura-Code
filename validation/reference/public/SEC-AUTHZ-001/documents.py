DOCUMENTS = {
    "d1": {"owner": "alice", "text": "Alice private"},
    "d2": {"owner": "bob", "text": "Bob private"},
}

def get_document(user_id, document_id):
    doc = DOCUMENTS[document_id]
    if doc["owner"] != user_id:
        raise PermissionError("not authorized")
    return doc
