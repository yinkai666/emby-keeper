import re
from urllib.parse import parse_qs, urlparse

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.raw.functions.messages import RequestAppWebView, GetBotApp
from pyrogram.raw.types import InputBotAppShortName, InputBotAppID, WebViewResultUrl
from pyrogram.raw.types.bot_app import BotApp
from pyrogram.raw.types.messages import BotApp as MessageBotApp
from aiohttp import ClientSession
from aiohttp_socks import ProxyTimeoutError, ProxyError
from faker import Faker

from embykeeper.utils import get_connector

from ..link import Link
from ._base import BotCheckin

__ignore__ = True


class TembyCheckin(BotCheckin):
    name = "Temby"
    bot_username = "HiEmbyBot"
    bot_checkin_cmd = "/hi"
    max_retries = 1
    additional_auth = ["captcha"]
    bot_success_keywords = ["签到成功"]
    bot_account_fail_keywords = ["需要邀请码", "关闭注册"]

    async def message_handler(self, client: Client, message: Message):
        if message.text and message.text == "请在一分钟内点击下方按钮完成签到":
            if message.reply_markup:
                buttons = [b for l in message.reply_markup.inline_keyboard for b in l]
                if len(buttons) == 1:
                    button = buttons[0]
                    if button.text == "签到":
                        if button.url:
                            url = await self.get_app_url(button.url)
                            passed = await self.solve_captcha(url)
                            if passed:
                                self.log.log("验证成功, 等待机器人响应.")
                                return
                            else:
                                self.log.error("签到失败: 验证码解析失败, 正在重试.")
                                await self.retry()
                                return

        return await super().message_handler(client, message)

    async def get_app_url(self, url: str):
        match = re.search(r"t\.me/(\w+)/(\w+)\?startapp=(\w+)", url)
        if not match:
            return None
        bot_username, app_short_name, start_param = match.groups()
        bot_peer = await self.client.resolve_peer(bot_username)
        app_spec = InputBotAppShortName(bot_id=bot_peer, short_name=app_short_name)
        message_app: MessageBotApp = await self.client.invoke(GetBotApp(app=app_spec, hash=0))
        app: BotApp = message_app.app
        input_app = InputBotAppID(id=app.id, access_hash=app.access_hash)
        webview: WebViewResultUrl = await self.client.invoke(
            RequestAppWebView(peer=bot_peer, start_param=start_param, platform="ios", app=input_app)
        )
        return webview.url

    async def solve_captcha(self, url: str):
        token = await Link(self.client).captcha("temby")
        if not token:
            return None
        else:
            scheme = urlparse(url)
            params = parse_qs(scheme.query)
            messageid = params.get("tgWebAppStartParam", [None])[0]
            url_submit = scheme._replace(query="", fragment="").geturl()
            connector = get_connector(self.proxy)
            useragent = Faker().safari()
            headers = {
                "Referer": url,
                "User-Agent": useragent,
            }
            params = {
                "messageid": messageid,
                "url": "",
                "cf-turnstile-response": token,
            }
            try:
                async with ClientSession(connector=connector) as session:
                    async with session.get(url_submit, headers=headers, params=params) as resp:
                        result = await resp.text()
                        if "好像还没有通过验证" in result:
                            return False
                        elif "签到失败" in result:
                            return False
                        else:
                            return True
            except (ProxyTimeoutError, ProxyError, OSError):
                return False
