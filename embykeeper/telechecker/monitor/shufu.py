import asyncio
from pyrogram.types import Message

from ._base import Monitor


class ShufuMonitor(Monitor):
    name = "叔服"
    chat_name = -1001890341413
    chat_keyword = r"SHUFU-\d+-Register_[\w]+"
    bot_username = "dashu660_bot"
    notify_create_name = True
    additional_auth = ["prime"]

    async def on_trigger(self, message: Message, key, reply):
        await self.client.send_message(self.bot_username, f"/invite {key}")
        self.log.bind(msg=True).info(f'已向 Bot @{self.bot_username} 发送了邀请码: "{key}", 请查看.')
