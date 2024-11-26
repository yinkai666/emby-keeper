from pyrogram.types import Message

from embykeeper.utils import to_iterable

from ._base import BotCheckin


class TanhuaCheckin(BotCheckin):
    name = "探花"
    bot_username = "TanhuaTvBot"
    additional_auth = ["prime"]
    bot_checkin_cmd = ["/start"]
    templ_panel_keywords = ["请选择功能", "用户面板", "用户名称"]
    bot_use_captcha = False

    async def message_handler(self, client, message: Message):
        text = message.caption or message.text
        if (
            text
            and any(keyword in text for keyword in to_iterable(self.templ_panel_keywords))
            and message.reply_markup
        ):
            keys = [k.text for r in message.reply_markup.inline_keyboard for k in r]
            for k in keys:
                if "个人信息" in k:
                    try:
                        await message.click(k)
                    except TimeoutError:
                        pass
                    return
                if "签到" in k or "簽到" in k:
                    try:
                        await message.click(k)
                    except TimeoutError:
                        self.log.debug(f"点击签到按钮无响应, 可能按钮未正确处理点击回复. 一般来说不影响签到.")
                    return
            else:
                self.log.warning(f"签到失败: 账户错误.")
                return await self.fail()

        if message.text and "请先加入聊天群组和通知频道" in message.text:
            self.log.warning(f"签到失败: 账户错误.")
            return await self.fail()

        await super().message_handler(client, message)
