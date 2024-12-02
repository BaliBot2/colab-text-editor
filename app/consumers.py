import json
from channels.generic.websocket import AsyncWebsocketConsumer
from app.document.document import ServerDocument



class EditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doc_id = self.scope['url_route']['kwargs']['doc_id']
        self.room_group_name = f'editor_{self.doc_id}'
        
        # Initialize document
        self.document = ServerDocument(doc_id=self.doc_id)
        await self.document.load_or_create_document()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages with OT.
        """
        try:
            text_data_json = json.loads(text_data)
            incoming_delta = text_data_json['content']

            # Apply changes to document
            success = await self.document.handle_changes(incoming_delta)
            
            if success:
                # Broadcast the Delta to all clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'editor_message',
                        'content': incoming_delta,
                        'sender_channel': self.channel_name,
                    }
                )
            else:
                # Send error message back to sender
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

    async def editor_message(self, event):
        if event['sender_channel'] != self.channel_name:
            content = event['content']
            await self.send(text_data=json.dumps({
                'content': content
            }))