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
        # Remove the WebSocket from the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Called when a message is received from the WebSocket.
        Updates the document content and broadcasts the changes to the group.
        """
        text_data_json = json.loads(text_data)
        content = text_data_json['content']

        # Log the received message (for debugging)
        print(f"Received content for doc_id {self.doc_id}: {content}")

        # Update the document content in the database
        try:
            document = ServerDocument(doc_id=self.doc_id)
            document.handle_changes(content)
        except ValueError as e:
            print(f"Error updating document {self.doc_id}: {e}")

        # Broadcast the updated content to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'editor_message',
                'content': content
            }
        )

    async def editor_message(self, event):
        """
        Called when a message is sent to the group.
        Sends the message to the WebSocket.
        """
        content = event['content']
        # Send the updated content back to the WebSocket client
        await self.send(text_data=json.dumps({
            'content': content
        }))