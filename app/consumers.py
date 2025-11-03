# consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from app.document.document import ServerDocument
from channels.db import database_sync_to_async
from app.models import DocumentAccess, ServerDocument as ServerDocumentModel

class EditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doc_id = self.scope['url_route']['kwargs']['doc_id']
        self.room_group_name = f'editor_{self.doc_id}'
        self.user_group_name = f'user_{self.scope["user"].username}'  # Add personal group
        self.username = self.scope["user"].username
        
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
            
        self.can_edit = await self.has_edit_access()
        if not await self.has_document_access():
            await self.close()
            return

        self.document = ServerDocument(doc_id=self.doc_id)
        await self.document.load_or_create_document(owner=self.scope["user"])

        # Join both the document group and personal group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'access_level',
            'canEdit': self.can_edit
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'cursor':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cursor_position',
                        'position': data.get('position'),
                        'username': self.username,
                        'sender_channel': self.channel_name,
                    }
                )
            elif message_type == 'check_permissions':
                # Handle permission check requests
                new_can_edit = await self.has_edit_access()
                await self.send(text_data=json.dumps({
                    'type': 'access_level',
                    'canEdit': new_can_edit
                }))
            else:
                # Recheck permissions before handling changes
                self.can_edit = await self.has_edit_access()
                if not self.can_edit:
                    await self.send(text_data=json.dumps({
                        'error': 'You do not have permission to edit this document'
                    }))
                    return
                    
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
            logging.error(f"Error receiving message: {e}")
            await self.send(text_data=json.dumps({
                'error': 'An unexpected error occurred.'
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

    async def permissions_updated(self, event):
        """Handle permission update notifications"""
        await self.send(text_data=json.dumps({
            'type': 'permissions_updated'
        }))

    @database_sync_to_async
    def has_document_access(self):
        try:
            document = ServerDocumentModel.objects.get(doc_id=self.doc_id)
            user = self.scope["user"]
            return (document.visibility == 'PUBLIC' or 
                   document.owner == user or 
                   DocumentAccess.objects.filter(document=document, user=user).exists())
        except ServerDocumentModel.DoesNotExist:
            return False
        except Exception as e:
            logging.error(f"Error checking document access: {e}")
            return False
            
    @database_sync_to_async
    def has_edit_access(self):
        try:
            document = ServerDocumentModel.objects.get(doc_id=self.doc_id)
            user = self.scope["user"]
            return (document.owner == user or 
                   DocumentAccess.objects.filter(
                       document=document, 
                       user=user,
                       access_type='EDITOR'
                   ).exists())
        except ServerDocumentModel.DoesNotExist:
            return False
        except Exception as e:
            logging.error(f"Error checking edit access: {e}")
            return False