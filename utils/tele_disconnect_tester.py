import asyncio
from pathlib import Path

from embykeeper.telechecker.tele import ClientsSession
from embykeeper.utils import AsyncTyper
import tomli as tomllib

app = AsyncTyper()

@app.async_command()
async def main(config: Path):
    with open(config, "rb") as f:
        config = tomllib.load(f)
    print("Send 1")
    async with ClientsSession.from_config(config) as clients:
        async for client in clients:
            await client.send_message("me", "Test")
            break
    print("Wait for 300 seconds")
    await asyncio.sleep(300)
    async with ClientsSession.from_config(config) as clients:
        async for client in clients:
            await client.send_message("me", "Test")
            break
    print("Send 2")

if __name__ == '__main__':
    app()