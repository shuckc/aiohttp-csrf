import asyncio
from functools import wraps
from typing import Callable, Optional

from aiohttp import web

from .policy import AbstractPolicy
from .storage import AbstractStorage

__version__ = "0.1.1"

RENDTYPE = Optional[Callable[[web.Request], web.StreamResponse]]
ERRTYPE = Optional[type[Exception]]

APP_POLICY_KEY = web.AppKey("aiohttp_csrf_policy", AbstractPolicy)
APP_STORAGE_KEY = web.AppKey("aiohttp_csrf_storage", AbstractStorage)
APP_ERROR_EXCEPTION_KEY = web.AppKey("aiohttp_csrf_error_exception", type(Exception))
APP_ERROR_RENDERER_KEY = web.AppKey("aiohttp_csrf_error_renderer", object)

MIDDLEWARE_SKIP_PROPERTY = "csrf_middleware_skip"

UNPROTECTED_HTTP_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")


def setup(
    app: web.Application,
    policy: AbstractPolicy,
    storage: AbstractStorage,
    exception: ERRTYPE = web.HTTPForbidden,
    error_renderer: RENDTYPE = None,
) -> None:
    app[APP_POLICY_KEY] = policy
    app[APP_STORAGE_KEY] = storage

    if exception is None or not issubclass(exception, Exception):
        raise TypeError("Default exception must be instance of Exception.")
    app[APP_ERROR_EXCEPTION_KEY] = exception  # type: ignore[misc]

    if error_renderer is not None:
        if not callable(error_renderer):
            raise TypeError("error_renderer must be callable.")
        app[APP_ERROR_RENDERER_KEY] = error_renderer


def _get_policy(request: web.Request) -> AbstractPolicy:
    try:
        return request.app[APP_POLICY_KEY]
    except KeyError:
        raise RuntimeError(
            "Policy not found. Install aiohttp_csrf in your "
            "aiohttp.web.Application using aiohttp_csrf.setup()"
        )


def _get_storage(request: web.Request) -> AbstractStorage:
    try:
        return request.app[APP_STORAGE_KEY]
    except KeyError:
        raise RuntimeError(
            "Storage not found. Install aiohttp_csrf in your "
            "aiohttp.web.Application using aiohttp_csrf.setup()"
        )


async def _render_error(
    request: web.Request, exception: ERRTYPE, renderer: RENDTYPE = None
) -> web.StreamResponse:
    if exception is None:
        try:
            exception = request.app[APP_ERROR_EXCEPTION_KEY]
        except KeyError:
            raise RuntimeError(
                "Default error renderer not found. Install aiohttp_csrf in "
                "your aiohttp.web.Application using aiohttp_csrf.setup()"
            )
        exception = web.HTTPForbidden

    if renderer is None:
        raise exception()

    if asyncio.iscoroutinefunction(renderer):
        return await renderer(request)
    else:
        return renderer(request)


async def get_token(request: web.Request) -> str:
    storage = _get_storage(request)

    return await storage.get(request)


async def generate_token(request: web.Request) -> str:
    storage = _get_storage(request)

    return await storage.generate_new_token(request)


async def save_token(request: web.Request, response: web.Response) -> None:
    storage = _get_storage(request)

    await storage.save_token(request, response)


def csrf_exempt(handler):
    @wraps(handler)
    async def wrapped_handler(*args, **kwargs):
        return await handler(*args, **kwargs)

    setattr(wrapped_handler, MIDDLEWARE_SKIP_PROPERTY, True)

    return wrapped_handler


async def _check(request: web.Request) -> bool:
    if not isinstance(request, web.Request):
        raise RuntimeError("Can't get request from handler params")

    original_token = await get_token(request)

    policy = _get_policy(request)

    return await policy.check(request, original_token)


def csrf_protect(
    handler=None, exception: ERRTYPE = None, error_renderer: RENDTYPE = None
):
    if error_renderer is not None and not callable(error_renderer):
        raise TypeError("Renderer must be callable")

    if exception is not None and not issubclass(exception, Exception):
        raise TypeError("exception must be BaseException class")

    def wrapper(handler):
        @wraps(handler)
        async def wrapped(*args, **kwargs):
            request = args[-1]

            if isinstance(request, web.View):
                request = request.request

            if request.method not in UNPROTECTED_HTTP_METHODS and not await _check(
                request
            ):
                return await _render_error(request, exception, error_renderer)

            raise_response = False

            try:
                response = await handler(*args, **kwargs)
            except web.HTTPException as exc:
                response = exc
                raise_response = True

            if isinstance(response, web.Response):
                await save_token(request, response)

            if raise_response:
                raise response

            return response

        setattr(wrapped, MIDDLEWARE_SKIP_PROPERTY, True)

        return wrapped

    if handler is None:
        return wrapper

    return wrapper(handler)


@web.middleware
async def csrf_middleware(request: web.Request, handler):
    if not getattr(handler, MIDDLEWARE_SKIP_PROPERTY, False):
        handler = csrf_protect(handler=handler)

    return await handler(request)
