# Update consumers.py to handle cursor messages
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from app.document.document import ServerDocument
from channels.db import database_sync_to_async
from app.models import DocumentAccess, ServerDocument as ServerDocumentModel

class EditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doc_id = self.scope['url_route']['kwargs']['doc_id']
        self.room_group_name = f'editor_{self.doc_id}'
        self.username = self.scope["user"].username
        
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
            
        if not await self.has_document_access():
            await self.close()
            return

        self.document = ServerDocument(doc_id=self.doc_id)
        await self.document.load_or_create_document()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'cursor':
                # Handle cursor position updates
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cursor_position',
                        'position': data.get('position'),
                        'username': self.username,
                        'sender_channel': self.channel_name,
                    }
                )
            else:
                # Handle regular document changes
                incoming_delta = data.get('content')
                if incoming_delta:
                    success = await self.document.handle_changes(incoming_delta)
                    
                    if success:
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'editor_message',
                                'content': incoming_delta,
                                'sender_channel': self.channel_name,
                            }
                        )
                    else:
                        await self.send(text_data=json.dumps({
                            'error': 'Failed to process changes'
                        }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def cursor_position(self, event):
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'cursor',
                'position': event['position'],
                'username': event['username']
            }))

    async def editor_message(self, event):
        if event['sender_channel'] != self.channel_name:
            content = event['content']
            await self.send(text_data=json.dumps({
                'type': 'content',
                'content': content
            }))

    @database_sync_to_async
    def has_document_access(self):
        try:
            document = ServerDocumentModel.objects.get(doc_id=self.doc_id)
            user = self.scope["user"]
            return (document.visibility == 'PUBLIC' or 
                   document.owner == user or 
                   DocumentAccess.objects.filter(document=document, user=user).exists())
        except Exception:
            return False