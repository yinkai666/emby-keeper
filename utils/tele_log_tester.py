import asyncio
from pathlib import Path

from embykeeper.telechecker.tele import ClientsSession
from embykeeper.telechecker.link import Link
from embykeeper.utils import AsyncTyper
import tomli as tomllib

app = AsyncTyper()


@app.async_command()
async def main(config: Path):
    with open(config, "rb") as f:
        config = tomllib.load(f)
    ClientsSession.watch = asyncio.create_task(ClientsSession.watchdog(40))
    print("Sending Test1")
    async with ClientsSession.from_config(config) as clients:
        async for client in clients:
            await Link(client).send_msg("Test1")
            break
    print("Wait for 40 seconds")
    await asyncio.sleep(40)
    print("Watchdog should be triggered")
    print("Wait for another 20 seconds")
    await asyncio.sleep(20)
    async with ClientsSession.from_config(config) as clients:
        async for client in clients:
            await Link(client).send_msg("Test1")
            break
    print("Sent Test2")


if __name__ == "__main__":
    app()
