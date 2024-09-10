import uuid
from unittest import mock

from blake3 import blake3

import aiohttp_csrf

COOKIE_NAME = "csrf_token"
HEADER_NAME = "X-CSRF-TOKEN"


def test_simple_token_generator() -> None:
    token_generator = aiohttp_csrf.token_generator.SimpleTokenGenerator()

    u = uuid.uuid4()

    with mock.patch("uuid.uuid4", return_value=u):
        token = token_generator.generate()

        assert u.hex == token


def test_hashed_token_generator() -> None:
    encoding = aiohttp_csrf.token_generator.HashedTokenGenerator.encoding

    token_generator = aiohttp_csrf.token_generator.HashedTokenGenerator(
        "secret",
    )

    u = uuid.uuid4()
    token_string = u.hex + "secret"

    hasher = blake3(token_string.encode(encoding=encoding))

    with mock.patch("uuid.uuid4", return_value=u):
        token = token_generator.generate()
        assert token == hasher.hexdigest()
