import abc
from typing import Optional, Protocol

from aiohttp import web

from .token_generator import HashedTokenGenerator, TokenGenerator

try:
    from aiohttp_session import get_session
except ImportError:  # pragma: no cover
    pass


REQUEST_NEW_TOKEN_KEY = "aiohttp_csrf_new_token"


class AbstractStorage(Protocol):
    async def generate_new_token(self, request: web.Request) -> str: ...

    async def get(self, request: web.Request) -> str: ...

    async def save_token(
        self, request: web.Request, response: web.Response
    ) -> None: ...


class BaseStorage:
    def __init__(
        self,
        token_generator: Optional[TokenGenerator] = None,
        secret_phrase: Optional[str] = None,
    ):
        if token_generator is None:
            if secret_phrase is None:
                raise TypeError(
                    "secret_phrase is required for default token type (Hash)"
                )
            token_generator = HashedTokenGenerator(secret_phrase)

        self.token_generator = token_generator

    def _generate_token(self) -> str:
        return self.token_generator.generate()

    async def generate_new_token(self, request: web.Request) -> str:
        if REQUEST_NEW_TOKEN_KEY in request:
            # perhaps request will support web.AppKey later?
            return str(request[REQUEST_NEW_TOKEN_KEY])

        token = self._generate_token()

        request[REQUEST_NEW_TOKEN_KEY] = token

        return token

    @abc.abstractmethod
    async def _get(self, request: web.Request) -> str: ...

    async def get(self, request: web.Request) -> str:
        token = await self._get(request)

        await self.generate_new_token(request)

        return token

    @abc.abstractmethod
    async def _save_token(
        self, request: web.Request, response: web.StreamResponse, token: str
    ) -> None: ...

    async def save_token(
        self, request: web.Request, response: web.StreamResponse
    ) -> None:
        old_token = await self._get(request)

        if REQUEST_NEW_TOKEN_KEY in request:
            token = request[REQUEST_NEW_TOKEN_KEY]
        elif old_token is None:
            token = await self.generate_new_token(request)
        else:
            token = None

        if token is not None:
            await self._save_token(request, response, token)


class CookieStorage(BaseStorage):
    def __init__(self, cookie_name: str, cookie_kwargs=None, *args, **kwargs):
        self.cookie_name = cookie_name
        self.cookie_kwargs = cookie_kwargs or {}

        super().__init__(*args, **kwargs)

    async def _get(self, request: web.Request) -> str:
        return request.cookies.get(self.cookie_name, "")

    async def _save_token(
        self, request: web.Request, response: web.StreamResponse, token: str
    ) -> None:
        response.set_cookie(
            self.cookie_name,
            token,
            **self.cookie_kwargs,
        )


class SessionStorage(BaseStorage):
    def __init__(self, session_name: str, *args, **kwargs):
        self.session_name = session_name

        super().__init__(*args, **kwargs)

    async def _get(self, request: web.Request) -> str:
        session = await get_session(request)

        return session.get(self.session_name, None)

    async def _save_token(
        self, request: web.Request, response: web.StreamResponse, token: str
    ) -> None:
        session = await get_session(request)

        session[self.session_name] = token
