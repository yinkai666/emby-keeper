import logging

from loguru import logger

from ..log import formatter
from .log import TelegramStream

logger = logger.bind(scheme="telegram")


async def start_notifier(config: dict):
    """消息通知初始化函数."""

    def _filter_log(record):
        notify = record.get("extra", {}).get("log", None)
        if notify or record["level"].no == logging.ERROR:
            return True
        else:
            return False

    def _filter_msg(record):
        notify = record.get("extra", {}).get("msg", None)
        if notify:
            return True
        else:
            return False

    def _formatter(record):
        return "{level}#" + formatter(record)

    accounts = config.get("telegram", [])
    notifier = config.get("notifier", None)
    if notifier:
        try:
            if notifier == True:
                notifier = accounts[0]
            elif isinstance(notifier, int):
                notifier = accounts[notifier + 1]
            elif isinstance(notifier, str):
                for a in accounts:
                    if a["phone"] == notifier:
                        notifier = a
                        break
            else:
                notifier = None
        except IndexError:
            notifier = None
    if notifier:
        logger.info(f'计划任务的关键消息将通过 Embykeeper Bot 发送至 "{notifier["phone"]}" 账号.')
        stream_log = TelegramStream(
            account=notifier,
            proxy=config.get("proxy", None),
            basedir=config.get("basedir", None),
            instant=config.get("notify_immediately", False),
        )
        logger.add(
            stream_log,
            format=_formatter,
            filter=_filter_log,
        )
        stream_msg = TelegramStream(
            account=notifier,
            proxy=config.get("proxy", None),
            basedir=config.get("basedir", None),
            instant=True,
        )
        logger.add(
            stream_msg,
            format=_formatter,
            filter=_filter_msg,
        )
        return stream_log, stream_msg
    else:
        return None
