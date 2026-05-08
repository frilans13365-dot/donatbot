from aiohttp import web


async def payment_webhook(request: web.Request) -> web.Response:
    return web.Response(text="OK")
