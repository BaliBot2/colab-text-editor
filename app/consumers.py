import json
from channels.generic.websocket import AsyncWebsocketConsumer
from app.document.document import ServerDocument

class EditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when the WebSocket connection is opened.
        Assigns the client to a room group based on doc_id and joins the group.
        """
        self.doc_id = self.scope['url_route']['kwargs']['doc_id']  # Extract doc_id from URL
        self.room_group_name = f'editor_{self.doc_id}'  # Create a unique group name per document

        # Add the WebSocket to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection is closed.
        Removes the client from the room group.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages with OT.
        """
        text_data_json = json.loads(text_data)
        incoming_delta = text_data_json['content']

        try:
            # Load and update the document asynchronously
            document = ServerDocument(doc_id=self.doc_id)
            await document.load_or_create_document()
            print(f"Recieving Delta on 2: {incoming_delta}")
            # Apply the incoming Delta to the current document state
            document.handle_changes(incoming_delta)

            # Save the updated state to the database asynchronously
            await document.save_to_database()

            # Broadcast the Delta to all clients
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'editor_message',
                    'content': incoming_delta,
                    'sender_channel': self.channel_name,# Exclude sender
                }
            )
        except ValueError as e:
            print(f"Error processing document: {e}")

    async def editor_message(self, event):
        """
        Broadcasts Deltas to all clients except the sender.
        """
        if event['sender_channel'] != self.channel_name:
            content = event['content']
            print(f"Broadcasting Delta to Client: {content}")
            await self.send(text_data=json.dumps({
                'content': content
            }))
