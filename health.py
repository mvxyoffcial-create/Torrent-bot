import os

from aiohttp import web

PORT = int(os.environ.get("PORT", 8000))


async def health(request):
    return web.json_response({"status": "ok"})


async def root(request):
    return web.Response(text="Bot is running")


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    return app


async def start_health_server():
    """Starts the health server in the background. Doesn't block."""
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    return runner

