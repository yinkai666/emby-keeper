import asyncio
from pathlib import Path

import tomli as tomllib
from loguru import logger

from embykeeper.telechecker.tele import ClientsSession
from embykeeper.telechecker.link import Link
from embykeeper.utils import AsyncTyper
from embykeeper.telechecker.notify import start_notifier

app = AsyncTyper()

@app.async_command()
async def log(config: Path):
    with open(config, "rb") as f:
        config = tomllib.load(f)
    await start_notifier(config)
    logger.bind(log=True).info("Test logging.")
    
@app.async_command()
async def disconnect(config: Path):
    with open(config, "rb") as f:
        config = tomllib.load(f)
    ClientsSession.watch = asyncio.create_task(ClientsSession.watchdog(40))
    print("Sending Test1")
    async with ClientsSession.from_config(config) as clients:
        async for client in clients:
            await Link(client).send_msg("ERROR#Test1")
            break
    print("Wait for 40 seconds")
    await asyncio.sleep(40)
    print("Watchdog should be triggered")
    print("Wait for another 20 seconds")
    await asyncio.sleep(20)
    async with ClientsSession.from_config(config) as clients:
        async for client in clients:
            await Link(client).send_msg("ERROR#Test1")
            break
    print("Sent Test2")


if __name__ == "__main__":
    app()
