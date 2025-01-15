from .pornemby_exam import _PornembyExamAnswerMonitor

__ignore__ = True


class TestPornembyExamMonitor(_PornembyExamAnswerMonitor):
    name = "Pornemby 科举回答测试"
    chat_name = "api_group"
    chat_allow_outgoing = True
    chat_user = None