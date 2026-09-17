import os
from pathlib import Path

class TelegramClientService:
    def __init__(self, context):
        self.context = context
        self.client = None
        self.events = None

    def configure(self):
        from telethon import TelegramClient, events
        api_id = os.getenv('TETKO_API_ID')
        api_hash = os.getenv('TETKO_API_HASH')
        session = os.getenv('TETKO_SESSION', str(Path('data') / 'tetko'))
        if not api_id or not api_hash:
            raise RuntimeError('Укажи TETKO_API_ID и TETKO_API_HASH')
        Path(session).parent.mkdir(parents=True, exist_ok=True)
        self.client = TelegramClient(session, int(api_id), api_hash)
        self.events = events
        self.context.client = self.client
        self.context.services['telegram'] = self
        return self.client

    async def start(self):
        if self.client is None:
            self.configure()
        await self.client.start()
        self.context.services['me'] = await self.client.get_me()
        return self.client

    async def run_until_disconnected(self):
        await self.client.run_until_disconnected()

    async def stop(self):
        if self.client and self.client.is_connected():
            await self.client.disconnect()
