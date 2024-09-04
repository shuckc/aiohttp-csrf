import uuid
from typing import Protocol

from blake3 import blake3


class TokenGenerator(Protocol):
    def generate(self) -> str: ...


class SimpleTokenGenerator:
    def generate(self) -> str:
        return uuid.uuid4().hex


class HashedTokenGenerator:
    encoding = "utf-8"

    def __init__(self, secret_phrase: str):
        self.secret_phrase = secret_phrase

    def generate(self) -> str:
        token = uuid.uuid4().hex

        token += self.secret_phrase

        hasher = blake3(token.encode(self.encoding))

        return hasher.hexdigest()
