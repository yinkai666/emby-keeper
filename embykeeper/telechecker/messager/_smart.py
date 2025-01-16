import asyncio
from datetime import date, datetime, time
from pathlib import Path
from typing import List, Tuple

from loguru import logger
from pyrogram.types import User
import yaml

from ...data import get_data
from ...utils import show_exception, truncate_str, distribute_numbers
from ..link import Link
from ..tele import ClientsSession

__ignore__ = True


class SmartMessager:
    """自动智能水群类."""

    name: str = None  # 水群器名称
    chat_name: str = None  # 群聊的名称
    default_messages: str = None  # 语言风格参考话术列表资源名
    additional_auth: List[str] = []  # 额外认证要求
    min_interval: int = None  # 预设两条消息间的最小间隔时间
    max_interval: int = None  # 预设两条消息间的最大间隔时间
    at: Tuple[time, time] = None  # 可发送的时间范围
    msg_per_day: int = 10  # 每天发送的消息数量
    min_msg_gap = 5  # 最小消息间隔

    site_last_message_time = None
    site_lock = asyncio.Lock()

    def __init__(self, account, me: User = None, nofail=True, proxy=None, basedir=None, config: dict = None):
        """
        自动智能水群类.
        参数:
            account: 账号登录信息
            me: 当前用户
            nofail: 启用错误处理外壳, 当错误时报错但不退出
            basedir: 文件存储默认位置
            proxy: 代理配置
            config: 当前水群器的特定配置
        """
        self.account = account
        self.nofail = nofail
        self.proxy = proxy
        self.basedir = basedir
        self.config = config
        self.me = me

        self.min_interval = config.get(
            "min_interval", config.get("interval", self.min_interval or 60)
        )  # 两条消息间的最小间隔时间
        self.max_interval = config.get("max_interval", self.max_interval)  # 两条消息间的最大间隔时间
        self.log = logger.bind(scheme="telemessager", name=self.name, username=me.name)
        self.timeline: List[int] = []  # 消息计划序列
        self.example_messages = []

    async def get_spec_path(self, spec):
        """下载话术文件对应的本地或云端文件."""
        if not Path(spec).exists():
            return await get_data(self.basedir, spec, proxy=self.proxy, caller=f"{self.name}水群")
        else:
            return spec

    async def _start(self):
        """自动水群器的入口函数的错误处理外壳."""
        try:
            return await self.start()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if self.nofail:
                self.log.warning(f"发生错误, 自动水群器将停止.")
                show_exception(e, regular=False)
                return False
            else:
                raise

    async def start(self):
        """自动水群器的入口函数."""

        async with ClientsSession([self.account], proxy=self.proxy, basedir=self.basedir) as clients:
            async for tg in clients:
                if self.additional_auth:
                    for a in self.additional_auth:
                        if not await Link(tg).auth(a, log_func=self.log.info):
                            return False

            if self.max_interval and self.min_interval > self.max_interval:
                self.log.warning(f"发生错误: 最小间隔不应大于最大间隔, 自动水群将停止.")
                return False

            if not await self.init():
                self.log.warning(f"状态初始化失败, 自动水群将停止.")
                return False

            messages_spec = self.config.get("messages", self.default_messages)
            if messages_spec and (not isinstance(messages_spec, str)):
                self.log.warning(f"发生错误: 参考语言风格列表只能为字符串, 代表远端或本地文件.")
                return False

            if messages_spec:
                messages_file = await self.get_spec_path(messages_spec)
                with open(messages_file, "r") as f:
                    data = yaml.safe_load(f)
                    self.example_messages = data.get("messages", [])[:100]

            self.log.bind(username=tg.me.name).info(
                f"即将预测当前状态下应该发送的水群消息, 但不会实际发送, 仅用于测试."
            )

            await self.send(dummy=True)

        if self.at:
            start_time, end_time = self.at
        else:
            start_time = time(9, 0, 0)
            end_time = time(23, 0, 0)

        start_datetime = datetime.combine(date.today(), start_time)
        end_datetime = datetime.combine(date.today(), end_time)

        start_timestamp = start_datetime.timestamp()
        end_timestamp = end_datetime.timestamp()

        msg_per_day = self.config.get("msg_per_day", self.msg_per_day)

        self.timeline = distribute_numbers(
            start_timestamp, end_timestamp, msg_per_day, self.min_interval, self.max_interval
        )

        # 检查并调整早于当前时间的时间点到明天
        now_timestamp = datetime.now().timestamp()
        for i in range(len(self.timeline)):
            if self.timeline[i] < now_timestamp:
                self.timeline[i] += 86400

        self.timeline = sorted(self.timeline)

        if self.timeline:
            while True:
                dt = datetime.fromtimestamp(self.timeline[0])
                self.log.info(f"下一次发送将在 [blue]{dt.strftime('%m-%d %H:%M:%S')}[/] 进行.")
                sleep_time = max(self.timeline[0] - datetime.now().timestamp(), 0)
                await asyncio.sleep(sleep_time)
                await self.send()
                self.timeline.pop(0)
                if not self.timeline:
                    break

    async def init(self):
        """可重写的初始化函数, 返回 False 将视为初始化错误."""
        return True

    async def send(self, dummy: bool = False):
        async with ClientsSession([self.account], proxy=self.proxy, basedir=self.basedir) as clients:
            async for tg in clients:
                log = self.log.bind(username=tg.me.name)
                chat = await tg.get_chat(self.chat_name)

                context = []
                i = 0
                async for msg in tg.get_chat_history(chat.id, limit=50):
                    i += 1
                    if self.min_msg_gap and msg.outgoing and i < self.min_msg_gap:
                        log.info(f"低于发送消息间隔要求 ({i} < {self.min_msg_gap}), 将不发送消息.")
                        return
                    spec = []
                    text = str(msg.caption or msg.text or "")
                    spec.append(f"消息发送时间为 {msg.date}")
                    if msg.photo:
                        spec.append("包含一张照片")
                    if msg.reply_to_message_id:
                        rmsg = await tg.get_messages(chat.id, msg.reply_to_message_id)
                        spec.append(f"回复了消息: {truncate_str(str(rmsg.caption or rmsg.text or ''), 60)}")
                    spec = " ".join(spec)
                    ctx = truncate_str(text, 180)
                    if msg.from_user and msg.from_user.name:
                        ctx = f"{msg.from_user.name}说: {ctx}"
                    if spec:
                        ctx += f" ({spec})"
                    context.append(ctx)

                payload = {}
                if context:
                    payload["context"] = list(reversed(context))
                if self.example_messages:
                    payload["messages"] = self.example_messages

                answer, _ = await Link(tg).infer_msg(payload)

                if answer:
                    if len(answer) > 50:
                        log.info(f"智能推测水群内容过长, 将不发送消息.")
                    elif "SKIP" in answer:
                        log.info(f"智能推测此时不应该水群, 将不发送消息.")
                    else:
                        if dummy:
                            log.info(
                                f'当前情况下在聊天 "{chat.name}" 中推断可发送水群内容为: [gray50]{truncate_str(answer, 20)}[/]'
                            )
                        else:
                            log.info(
                                f'即将在5秒后向聊天 "{chat.name}" 发送: [gray50]{truncate_str(answer, 20)}[/]'
                            )
                            await asyncio.sleep(5)
                            msg = await tg.send_message(chat.id, answer)
                            log.info(f'已向聊天 "{chat.name}" 发送: [gray50]{truncate_str(answer, 20)}[/]')
                            return msg
                else:
                    log.warning(f"智能推测水群内容失败, 将不发送消息.")
