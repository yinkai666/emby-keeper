from ._smart import SmartMessager

__ignore__ = True

class SmartPornembyMessager(SmartMessager):
    name = "Pornemby"
    chat_name = "pornemby"
    default_messages = "pornemby-common-wl@latest.yaml"
    additional_auth = ["pornemby_pack"]
    msg_per_day = 100