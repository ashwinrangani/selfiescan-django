import json
from channels.generic.websocket import AsyncWebsocketConsumer
import httpx

class ChatConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    'http://43.204.107.230:5678/webhook/2f9eaa78-a070-4824-9c06-21ea32693527',
                    json={'message': message},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()

                    # If response is a list, take first item's "output"
                    if isinstance(data, list) and len(data) > 0:
                        reply = data[0].get('output') or "🤖 (Empty reply)"
                    else:
                        reply = data.get('reply') or data.get('message') or "🤖 (Empty reply)"
                else:
                    reply = f"⚠️ AI agent error: {resp.status_code}"
            except Exception as e:
                reply = f"⚠️ Could not reach AI agent: {str(e)}"

        await self.send(text_data=json.dumps({'message': reply}))
