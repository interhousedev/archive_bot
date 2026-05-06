import asyncio
import argparse

from app.settings import settings
from app.bootstrap import bootstrap


async def run_bot() -> None:
    from app.bot.bot import main as bot_main
    container = await bootstrap(settings)
    await bot_main(botapi_token=settings.botapi_token, container=container)


async def run_web() -> None:
    import uvicorn
    from app.web.app import create_app
    container = await bootstrap(settings)
    web_app = create_app(container)
    config = uvicorn.Config(web_app, host=settings.web_host, port=settings.web_port)
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory Archive")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--telegram-bot", action="store_true", help="Run Telegram bot")
    group.add_argument("--web", action="store_true", help="Run FastAPI web server")
    args = parser.parse_args()

    if args.telegram_bot:
        asyncio.run(run_bot())
    elif args.web:
        asyncio.run(run_web())


if __name__ == "__main__":
    main()
