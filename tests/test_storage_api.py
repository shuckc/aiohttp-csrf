from unittest.mock import MagicMock

from aiohttp.test_utils import make_mocked_request
from aiohttp.web import StreamResponse

import aiohttp_csrf


class FakeStorage(aiohttp_csrf.storage.BaseStorage):
    async def _get(self, request):
        return request.get("my_field")

    async def _save_token(self, request, response, token):
        request["my_field"] = token


async def test_1() -> None:
    storage = FakeStorage(secret_phrase="test")

    storage._generate_token = MagicMock(return_value="1")  # type: ignore[method-assign]
    storage._get = MagicMock(return_value="1")  # type: ignore[method-assign]

    assert storage._generate_token.call_count == 0

    request = make_mocked_request("/", "GET")

    await storage.generate_new_token(request)

    assert storage._generate_token.call_count == 1

    await storage.generate_new_token(request)
    await storage.generate_new_token(request)

    assert storage._generate_token.call_count == 1


async def test_2() -> None:
    storage = FakeStorage(secret_phrase="test")

    storage._generate_token = MagicMock(return_value="1")  # type: ignore[method-assign]

    request = make_mocked_request("/", "GET")
    resp = StreamResponse()

    assert storage._generate_token.call_count == 0

    await storage.save_token(request, resp)

    assert storage._generate_token.call_count == 1

    request2 = make_mocked_request("/", "GET")

    request2["my_field"] = 1

    await storage.save_token(request2, resp)


# we no longer assert subclass, so this no longer raises an error
# async def test_3() -> None:
#     class Some:
#         pass
#
#     token_generator = Some()
#
#     with pytest.raises(TypeError):
#         FakeStorage(token_generator=token_generator)
