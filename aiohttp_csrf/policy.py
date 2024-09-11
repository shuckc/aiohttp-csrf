import logging
from secrets import compare_digest
from typing import Protocol

from aiohttp import web


class AbstractPolicy(Protocol):
    async def check(self, request: web.Request, original_value: str) -> bool: ...


class FormPolicy:
    def __init__(self, field_name: str):
        self.field_name = field_name

    async def check(self, request: web.Request, original_value: str) -> bool:
        get = request.match_info.get(self.field_name, None)
        post_req = await request.post() if get is None else None
        post = post_req.get(self.field_name) if post_req is not None else None
        post = post if post is not None else ""
        token = get if get is not None else post
        if not isinstance(token, str):
            logging.debug("CSRF failure: Missing token on request form")
            return False
        return compare_digest(token, original_value)


class HeaderPolicy:
    def __init__(self, header_name: str):
        self.header_name = header_name

    async def check(self, request: web.Request, original_value: str) -> bool:
        token = request.headers.get(self.header_name)
        if not isinstance(token, str):
            logging.debug("CSRF failure: Missing token on request headers")
            return False
        return compare_digest(token, original_value)


class FormAndHeaderPolicy(HeaderPolicy, FormPolicy):
    def __init__(self, header_name: str, field_name: str):
        self.header_name = header_name
        self.field_name = field_name

    async def check(self, request: web.Request, original_value: str) -> bool:
        header_check = await HeaderPolicy.check(
            self,
            request,
            original_value,
        )

        if header_check:
            return True

        form_check = await FormPolicy.check(self, request, original_value)

        if form_check:
            return True

        return False
