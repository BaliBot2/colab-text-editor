import json
from channels.generic.websocket import AsyncWebsocketConsumer
from app.document.document import ServerDocument
from channels.db import database_sync_to_async
from app.models import DocumentAccess, ServerDocument as ServerDocumentModel

class EditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doc_id = self.scope['url_route']['kwargs']['doc_id']
        self.room_group_name = f'editor_{self.doc_id}'
        
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
            
        if not await self.has_document_access():
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial state to new connection
        document = ServerDocument(doc_id=self.doc_id)
        await document.load_or_create_document()
        await self.send(text_data=json.dumps({
            'content': document.state
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

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            # Handle content updates
            if 'content' in data:
                document = ServerDocument(doc_id=self.doc_id)
                await document.load_or_create_document()
                success = await document.handle_changes(data['content'])
                
                if success:
                    # Send the complete document state
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'editor_message',
                            'content': document.state,  # Send full state
                            'sender_channel': self.channel_name,
                        }
                    )
            
            # Handle cursor updates
            elif 'cursor' in data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cursor_message',
                        'cursor': data['cursor'],
                        'sender_channel': self.channel_name,
                    }
                )
            
            # Handle cursor removal
            elif 'cursor_remove' in data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cursor_remove_message',
                        'user_id': data['cursor_remove'],
                        'sender_channel': self.channel_name,
                    }
                )
                
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to process message'
            }))

    async def editor_message(self, event):
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'content': event['content']
            }))

    async def cursor_message(self, event):
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'cursor': event['cursor']
            }))

    async def cursor_remove_message(self, event):
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'user_left': event['user_id']
            }))