# Task

Harden `get_document(user_id, document_id)`.

A user may retrieve a document only when that user owns the document.
Unknown documents must still raise `KeyError`.
Unauthorized access must raise `PermissionError`.
Preserve the existing return shape and public behavior for the owner.
