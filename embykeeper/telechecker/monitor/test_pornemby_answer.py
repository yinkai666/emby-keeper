from .pornemby_answer import _PornembyAnswerAnswerMonitor

__ignore__ = True


class TestPornembyAnswerMonitor(_PornembyAnswerAnswerMonitor):
    name = "Pornemby 问题回答测试"
    chat_name = "api_group"
    chat_allow_outgoing = True
    chat_user = None