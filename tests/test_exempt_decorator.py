import pytest
from aiohttp import web

import aiohttp_csrf

COOKIE_NAME = "csrf_token"
HEADER_NAME = "X-CSRF-TOKEN"


@pytest.fixture
def create_app(init_app):
    def go(loop):
        async def handler_get(request):
            await aiohttp_csrf.generate_token(request)

            return web.Response(body=b"OK")

        @aiohttp_csrf.csrf_exempt
        async def handler_post(request):
            return web.Response(body=b"OK")

        handlers = [
            ("GET", "/", handler_get),
            ("POST", "/", handler_post),
        ]

        policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
        storage = aiohttp_csrf.storage.CookieStorage(
            COOKIE_NAME, {}, secret_phrase="test"
        )

        app = init_app(
            policy=policy,
            storage=storage,
            handlers=handlers,
            loop=loop,
        )

        app.middlewares.append(aiohttp_csrf.csrf_middleware)

        return app

    yield go


async def test_decorator_method_view(test_client, create_app) -> None:
    client = await test_client(
        create_app,
    )

    resp = await client.get("/")

    assert resp.status == 200

    # POST method handler has csrf_exempt marker
    resp = await client.post("/")

    assert resp.status == 200
