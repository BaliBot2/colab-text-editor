# views.py

from django.shortcuts import render, redirect
from django.http import Http404
from app.document.document import ServerDocument as ServerDocumentLogic  # Import logic

def new_document(request):
    """
    Creates a new document and redirects the user to its editor.
    """
    # create new doc on server
    server_doc_logic = ServerDocumentLogic()
    #save to db
    server_doc_logic.save_to_database()
    # automatically send to editor
    return redirect(f'/editor/{server_doc_logic.id}/')

def load_document(request, doc_id: str):
    """
    Loads a document by its ID and renders the editor.
    """
    try:
        # Validate doc
        server_doc_logic = ServerDocumentLogic(doc_id=doc_id)
        print(f"Loading document: {server_doc_logic.id}")  # for debug
        return render(request, 'index.html', {
            'doc_id': server_doc_logic.id,
            'content': server_doc_logic.data  # content currently is just a template
        })
    except ValueError as e:
        print(f"Error: {e}")  # Debugging
        raise Http404(str(e))

def index(request):
    """
    Handles the root URL. Creates a new document and redirects to its editor.
    """
    server_doc_logic = ServerDocumentLogic()
    server_doc_logic.save_to_database()
    return redirect(f'/editor/{server_doc_logic.id}/')
