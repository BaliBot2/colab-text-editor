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


async def load_document(request, doc_id):
    try:
        # Load or create the document
        server_doc_logic = ServerDocumentLogic(doc_id=doc_id)
        await server_doc_logic.load_or_create_document()
        return render(request, 'index.html', {
            'doc_id': server_doc_logic.id,
            'content': server_doc_logic.state
        })
    except ValueError as e:
        raise Http404(str(e))



def index(request):
    """
    Handles the root URL. Creates a new document and redirects to its editor.
    """
    server_doc_logic = ServerDocumentLogic()
    server_doc_logic.save_to_database()
    return redirect(f'/editor/{server_doc_logic.id}/')
