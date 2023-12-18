from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.forms.models import model_to_dict

class PositionsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from .models import Position  # Move the import here

        await self.accept()

        # Fetch positions from the database
        positions = Position.objects.all()

        # Send positions to the client
        await self.send(text_data=json.dumps({
            'positions': [model_to_dict(position) for position in positions]
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))