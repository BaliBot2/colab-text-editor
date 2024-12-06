# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
import json
from django.http import HttpResponse, Http404
from app.document.document import ServerDocument as ServerDocumentLogic
from app.models import ServerDocument, DocumentAccess
from asgiref.sync import sync_to_async
from django.db.models import Q
import json
from django.core.serializers.json import DjangoJSONEncoder
# Helper functions for async database operations
@sync_to_async
def get_document(doc_id):
    return ServerDocument.objects.get(doc_id=doc_id)

@sync_to_async
def check_access(document, user):
    return (document.visibility == 'PUBLIC' or 
            document.owner == user or 
            DocumentAccess.objects.filter(document=document, user=user).exists())


# views.py
@login_required(login_url='login')
async def load_document(request, doc_id):
    try:
        # Get document from database
        document = await get_document(doc_id)
        
        # Check permissions
        has_access = await check_access(document, request.user)
        if not has_access:
            return HttpResponse('Unauthorized', status=403)
        
        # Load document logic
        server_doc_logic = ServerDocumentLogic(doc_id=doc_id)
        await server_doc_logic.load_or_create_document()
        
        # Get content and ensure it has proper structure
        content = document.content if document.content else {"ops": []}
        
        # Serialize for template
        initial_content = json.dumps(content, cls=DjangoJSONEncoder)
        
        return render(request, 'index.html', {
            'doc_id': doc_id,
            'initial_content': initial_content,
            'user': request.user.username,
            'doc_title': document.title  # Add this line
        })
    except ServerDocument.DoesNotExist:
        raise Http404("Document not found")
    except ValueError as e:
        raise Http404(str(e))
@login_required(login_url='login')
def home(request):
    """
    Display all documents the user has access to
    """
    # Get documents user owns or has access to
    documents = ServerDocument.objects.filter(
        Q(owner=request.user) |  # Documents owned by user
        Q(documentaccess__user=request.user) |  # Documents shared with user
        Q(visibility='PUBLIC')  # Public documents
    ).distinct().order_by('-updated_at')
    
    return render(request, 'home.html', {
        'documents': documents,
        'user': request.user
    })

@login_required(login_url='login')
def new_document(request):
    """
    Creates a new document and redirects to the editor
    """
    server_doc_logic = ServerDocumentLogic()
    document = ServerDocument.objects.create(
        doc_id=server_doc_logic.id,
        title="Untitled Document",  
        content={"ops": []},
        owner=request.user,
        visibility='PRIVATE'
    )
    return redirect('load_document', doc_id=document.doc_id)

@login_required(login_url='login')
def index(request):
    """
    Handles the root URL. Creates a new document and redirects to its editor.
    """
    server_doc_logic = ServerDocumentLogic()
    
    # Create the database entry
    document = ServerDocument.objects.create(
        doc_id=server_doc_logic.id,
        content=server_doc_logic.state,
        owner=request.user,
        visibility='PRIVATE'
    )
    
    return redirect(f'/editor/{server_doc_logic.id}/')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home instead of index
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})
            
        user = User.objects.create_user(username=username, password=password, email=email)
        login(request, user)
        return redirect('home')
        
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
@require_http_methods(["POST"])
def share_document(request, doc_id):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        access_type = data.get('accessType')
        
        # Get document and verify ownership
        document = ServerDocument.objects.get(doc_id=doc_id, owner=request.user)
        
        # Get or create user by email
        user = User.objects.get(email=email)
        
        # Create or update access
        DocumentAccess.objects.update_or_create(
            document=document,
            user=user,
            defaults={'access_type': access_type}
        )
        
        return JsonResponse({'status': 'success'})
    except ServerDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_shared_users(request, doc_id):
    try:
        document = ServerDocument.objects.get(doc_id=doc_id, owner=request.user)
        shared_users = DocumentAccess.objects.filter(document=document).select_related('user')
        users_list = [{
            'id': access.id,
            'email': access.user.email,
            'access_type': access.access_type
        } for access in shared_users]
        return JsonResponse(users_list, safe=False)
    except ServerDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

@login_required
@require_http_methods(["DELETE"])
def remove_access(request, access_id):
    try:
        access = DocumentAccess.objects.get(
            id=access_id,
            document__owner=request.user
        )
        access.delete()
        return JsonResponse({'status': 'success'})
    except DocumentAccess.DoesNotExist:
        return JsonResponse({'error': 'Access not found'}, status=404)

@login_required
@require_http_methods(["DELETE"])
def delete_document(request, doc_id):
    try:
        document = ServerDocument.objects.get(doc_id=doc_id, owner=request.user)
        document.delete()
        return JsonResponse({'status': 'success'})
    except ServerDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found or you do not have permission to delete it'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

# views.py
@login_required
@require_http_methods(["POST"])
def update_title(request, doc_id):
    try:
        # Get document and verify access
        document = ServerDocument.objects.get(doc_id=doc_id)
        if not (document.owner == request.user or 
                DocumentAccess.objects.filter(document=document, user=request.user, access_type='EDITOR').exists()):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Get title from request data
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        
        if not new_title:
            new_title = "Untitled Document"
            
        # Update the document title
        document.title = new_title
        document.save()
        
        return JsonResponse({'status': 'success', 'title': new_title})
    except ServerDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)