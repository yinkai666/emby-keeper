from .misty import MistyMonitor

__ignore__ = True


class TestMistyMonitor(MistyMonitor):
    name = "Misty 测试"
    chat_name = "api_group"
    chat_allow_outgoing = True
    chat_user = []
