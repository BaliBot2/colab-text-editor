# document/document.py

from app.models import ServerDocument as ServerDocumentModel
from django.core.exceptions import ObjectDoesNotExist
from secrets import token_urlsafe
from delta import Delta
import re
from asgiref.sync import sync_to_async

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

# document/document.py
from app.models import ServerDocument as ServerDocumentModel
from django.core.exceptions import ObjectDoesNotExist
from secrets import token_urlsafe
import re
from asgiref.sync import sync_to_async

def validate_id(id: str) -> bool:
    url_safe_pattern = r'^[a-zA-Z0-9._~-]+$'
    return bool(re.match(url_safe_pattern, id))

def generate_id(n_bytes=8) -> str:
    return token_urlsafe(n_bytes)


class ServerDocument:
    def __init__(self, doc_id=None):
        self.id = doc_id or generate_id()
        self.state = {"ops": []}

    @sync_to_async
    def load_or_create_document(self):
        """
        Loads the document from the database or creates a new one if it does not exist.
        """
        if not validate_id(self.id):
            raise ValueError("Invalid document ID format.")

        try:
            db_doc = ServerDocumentModel.objects.get(doc_id=self.id)
            self.state = db_doc.content or {"ops": []}
            print(f"Loaded document state: {self.state}")
        except ServerDocumentModel.DoesNotExist:
            raise ValueError("Document not found")

    @sync_to_async
    def handle_changes(self, incoming_delta):
        """
        Apply incoming changes to the document using OT.
        """
        try:
            db_doc = ServerDocumentModel.objects.get(doc_id=self.id)
            current_state = Delta(db_doc.content.get("ops", []))
            new_delta = Delta(incoming_delta.get("ops", []))

            # Compose the deltas to get the new state
            new_state = current_state.compose(new_delta)
            
            # Update both local and database state
            self.state = {"ops": new_state.ops}
            db_doc.content = self.state
            db_doc.save()
            
            print(f"Applied changes to document {self.id}. New state: {self.state}")
            return True
        except Exception as e:
            print(f"Error handling changes: {e}")
            return False


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
