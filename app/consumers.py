import json
from channels.generic.websocket import AsyncWebsocketConsumer
from app.document.document import ServerDocument

class EditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doc_id = self.scope['url_route']['kwargs']['doc_id']
        self.room_group_name = f'editor_{self.doc_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if 'content' in data:
            try:
                document = ServerDocument(doc_id=self.doc_id)
                await document.load_or_create_document()
                await document.handle_changes(data['content'])
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'editor_message',
                        'content': data['content'],
                        'sender_channel': self.channel_name,
                    }
                )
            except Exception as e:
                print(f"Error processing document: {e}")
                
        elif 'cursor' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'cursor_message',
                    'cursor': data['cursor'],
                    'sender_channel': self.channel_name,
                }
            )
        
        elif 'cursor_remove' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'cursor_remove_message',
                    'user_id': data['cursor_remove'],
                    'sender_channel': self.channel_name,
                }
            )

    async def cursor_remove_message(self, event):
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'user_left': event['user_id']
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

    async def user_disconnect_message(self, event):
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'user_left': event['user_left']
            }))