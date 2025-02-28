from pyrogram import Client, __version__, idle
from pyrogram.raw.all import layer
from config import API_ID, API_HASH, BOT_TOKEN
from pyromod import listen
from plugins import web_server
from aiohttp import web


class Bot(Client):

    def __init__(self):
        super().__init__(
            name="forward-bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

  
    async def start(self):
        await super().start()
        me = await self.get_me()
        srvr = web.AppRunner(await web_server())
        await srvr.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(srvr, "0.0.0.0", "8080").start()     
        print(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    
    async def stop(self, *args):
        await super().stop()
        print("Bot stopped. Bye.")

app = Bot()
app.run()  
