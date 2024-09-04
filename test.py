from typing import Callable

from aiohttp import web


async def hello(request: web.Request) -> web.Response:
    return web.Response(text="Hello, world")


def dec(handler: Callable):
    def wrapped(*args, **kwargs) -> web.Response:
        request = args[-1]
        print(request)
        breakpoint()
        return handler(*args, **kwargs)

    return wrapped


class MyView(web.View):
    @dec
    async def get(self) -> web.Response:
        return web.Response(text="Get Hello, world")

    async def post(self) -> web.Response:
        return web.Response(text="Post Hello, world")


@web.middleware
async def middleware(request, handler):
    return await handler(request)


app = web.Application(middlewares=[middleware])
app.router.add_route("*", "/", MyView)

web.run_app(app)
