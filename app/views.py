from django.shortcuts import render, redirect
from django.http import Http404
from django.core.serializers.json import DjangoJSONEncoder
import json
from app.document.document import ServerDocument as ServerDocumentLogic

def new_document(request):
    """
    Creates a new document and redirects the user to its editor.
    """
    server_doc_logic = ServerDocumentLogic()
    server_doc_logic._save_to_database()  # Using internal sync method
    return redirect(f'/editor/{server_doc_logic.id}/')

async def load_document(request, doc_id):
    try:
        server_doc_logic = ServerDocumentLogic(doc_id=doc_id)
        await server_doc_logic.load_or_create_document()
        
        # Properly serialize the state to JSON
        initial_content = json.dumps(server_doc_logic.state, cls=DjangoJSONEncoder)
        
        return render(request, 'index.html', {
            'doc_id': server_doc_logic.id,
            'initial_content': initial_content  # Now properly serialized
        })
    except ValueError as e:
        raise Http404(str(e))
    
def index(request):
    """
    Handles the root URL. Creates a new document and redirects to its editor.
    """
    server_doc_logic = ServerDocumentLogic()
    server_doc_logic._save_to_database()  # Using internal sync method
    return redirect(f'/editor/{server_doc_logic.id}/')