import pytest
from aiohttp import web

import aiohttp_csrf

COOKIE_NAME = "csrf_token"
HEADER_NAME = "X-CSRF-TOKEN"


class FakeClass:
    pass


# there is no longer an extends check on the policy, so this no longer raises
# async def test_bad_policy(test_client, init_app) -> None:
#     policy = FakeClass()
#     storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME, {}, secret_phrase="test")
#
#     with pytest.raises(TypeError):
#         await test_client(
#             init_app,
#             policy=policy,
#             storage=storage,
#             handlers=[],
#         )


# there is no longer an extends check on the storage, so this no longer raises
# async def test_bad_storage(test_client, init_app) -> None:
#     policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
#     storage = FakeClass()
#
#     with pytest.raises(TypeError):
#         await test_client(
#             init_app,
#             policy=policy,
#             storage=storage,
#             handlers=[],
#         )


async def test_bad_error_renderer(test_client, init_app) -> None:
    policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
    storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME, {}, secret_phrase="test")

    with pytest.raises(TypeError):
        await test_client(
            init_app,
            policy=policy,
            storage=storage,
            error_renderer=1,
            handlers=[],
        )


async def test_app_without_setup(test_client) -> None:
    def create_app(loop):
        app = web.Application()

        @aiohttp_csrf.csrf_protect
        async def handler(request):
            await aiohttp_csrf.generate_token(request)

            return web.Response()

        app.router.add_route(
            "GET",
            "/",
            handler,
        )

        return app

    client = await test_client(
        create_app,
    )

    resp = await client.get("/")

    assert resp.status == 500
