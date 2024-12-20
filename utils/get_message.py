from pathlib import Path
import tomli as tomllib

from embykeeper.telechecker.tele import ClientsSession
from embykeeper.utils import AsyncTyper

app = AsyncTyper()

@app.async_command()
async def main(config: Path, url: str):
    with open(config, "rb") as f:
        config = tomllib.load(f)
    proxy = config.get("proxy", None)
    async with ClientsSession(config["telegram"][:1], proxy=proxy) as clients:
        async for tg in clients:
            try:
                # Parse message URL to get chat_id and message_id
                if not url.startswith('https://t.me/'):
                    print("Invalid Telegram message URL")
                    return
                
                parts = url.split('/')
                if len(parts) < 2:
                    print("Invalid URL format")
                    return
                
                chat_id = parts[-2]
                message_id = int(parts[-1])
                
                # Get message details
                message = await tg.get_messages(chat_id=chat_id, message_ids=message_id)
                if message:
                    print(message)
                else:
                    print("Message not found")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    app()
