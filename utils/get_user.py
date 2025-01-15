from pathlib import Path
import tomli as tomllib

from embykeeper.telechecker.tele import ClientsSession
from embykeeper.utils import AsyncTyper

app = AsyncTyper()


@app.async_command()
async def main(config: Path, spec: str):
    with open(config, "rb") as f:
        config = tomllib.load(f)
    proxy = config.get("proxy", None)
    async with ClientsSession(config["telegram"][:1], proxy=proxy) as clients:
        async for tg in clients:
            try:
                spec = int(spec)
            except:
                pass
            try:
                results = await tg.get_users(spec)
                print(results)
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    app()
