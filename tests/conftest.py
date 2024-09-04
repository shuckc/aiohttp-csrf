import asyncio
from typing import Generator

import pytest
from aiohttp import web

import aiohttp_csrf
from aiohttp_csrf import AbstractPolicy, AbstractStorage

SESSION_NAME = COOKIE_NAME = "csrf_token"
FORM_FIELD_NAME = HEADER_NAME = "X-CSRF-TOKEN"


@pytest.yield_fixture
def init_app() -> (
    Generator[[asyncio.Loop, AbstractPolicy, AbstractStorage], web.Application]
):
    def go(
        loop,
        policy,
        storage,
        handlers,
        error_renderer=None,
    ) -> web.Application:
        app = web.Application()

        kwargs = {
            "policy": policy,
            "storage": storage,
        }

        if error_renderer is not None:
            kwargs["error_renderer"] = error_renderer

        aiohttp_csrf.setup(app, **kwargs)

        for method, url, handler in handlers:
            app.router.add_route(
                method,
                url,
                handler,
            )

        return app

    yield go


@pytest.fixture(
    params=[
        (aiohttp_csrf.policy.FormPolicy, (FORM_FIELD_NAME,)),
        (aiohttp_csrf.policy.FormAndHeaderPolicy, (HEADER_NAME, FORM_FIELD_NAME)),
    ]
)
def csrf_form_policy(request):
    _class, args = request.param

    return _class(*args)


@pytest.fixture(
    params=[
        (aiohttp_csrf.policy.HeaderPolicy, (HEADER_NAME,)),
        (aiohttp_csrf.policy.FormAndHeaderPolicy, (HEADER_NAME, FORM_FIELD_NAME)),
    ]
)
def csrf_header_policy(request):
    _class, args = request.param

    return _class(*args)


@pytest.fixture(
    params=[
        (aiohttp_csrf.storage.SessionStorage, (SESSION_NAME,)),
        (aiohttp_csrf.storage.CookieStorage, (COOKIE_NAME,)),
    ]
)
def csrf_storage(request):
    _class, args = request.param

    return _class(*args)
