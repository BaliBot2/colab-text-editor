# document/document.py

from app.models import ServerDocument as ServerDocumentModel
from django.core.exceptions import ObjectDoesNotExist
from secrets import token_urlsafe
import re

def validate_id(id: str) -> bool:
    """
    Validates that the given document ID is URL-safe.
    """
    url_safe_pattern = r'^[a-zA-Z0-9._~-]+$'
    return bool(re.match(url_safe_pattern, id))

def generate_id(n_bytes=8) -> str:
    """
    Generates a secure, URL-safe unique ID for a document.
    """
    return token_urlsafe(n_bytes)

class ServerDocument:
    """
    A server-side representation of a document.
    Manages document creation, retrieval, and updates.
    """

    def __init__(self, doc_id=None):
        if doc_id:
            if not validate_id(doc_id):
                raise ValueError("Invalid document ID format.")
            self.id = doc_id
            try:
                # Load the document from the database
                db_doc = ServerDocumentModel.objects.get(doc_id=doc_id)
                self.data = db_doc.content or {}  # Load content as dict
            except ObjectDoesNotExist:
                raise ValueError(f"Document with ID {doc_id} does not exist.")
        else:
            # Generate a new document
            self.id = generate_id()
            self.data = {}  # New document with empty content

    def save_to_database(self):
        """
        Saves or updates the document in the database.
        """
        obj, created = ServerDocumentModel.objects.update_or_create(
            doc_id=self.id,
            defaults={"content": self.data}
        )
        return obj

    def handle_changes(self, new_data):
        """
        Handles updates to the document's content.
        """
        self.data = new_data
        self.save_to_database()

# Document Management Functions
def create_new_document():
    """
    Creates a new document and saves it to the database.
    Returns the document ID and initial content.
    """
    document = ServerDocument()  # Create a new document instance
    document.save_to_database()  # Save the document to the database
    return document.id, document.data  # Return ID and content

def lookup_document(doc_id):
    """
    Looks up a document by its unique ID.
    Returns the document's content if found.
    Raises a ValueError if the document does not exist.
    """
    try:
        document = ServerDocument(doc_id=doc_id)  # Load the document by ID
        return document.data
    except ValueError as e:
        raise e

def update_document(doc_id, new_content):
    """
    Updates the content of a document with the given ID.
    Saves the updated content to the database.
    Returns the updated content.
    """
    try:
        document = ServerDocument(doc_id=doc_id)  # Load the document by ID
        document.handle_changes(new_content)  # Update the document's content
        return document.data  # Return the updated content
    except ValueError as e:
        raise e
