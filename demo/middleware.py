import logging

from aiohttp import web

import aiohttp_csrf

FORM_FIELD_NAME = "_csrf_token"
COOKIE_NAME = "csrf_token"


# Example with middleware installed - needs @csrf_exempt where required
# does not use aiohttp-session
#
# response headers contain:
#   Set-Cookie: csrf_token=9880890793704407909e9dc4faa588b1cde1d371689fbda71f110a69e52b3485; Path=/
# form contains:
#   <input type="hidden" name="_csrf_token" value="9880890793704407909e9dc4faa588b1cde1d371689fbda71f110a69e52b3485" />


def make_app():
    logging.basicConfig(level=logging.INFO)
    csrf_policy = aiohttp_csrf.policy.FormPolicy(FORM_FIELD_NAME)

    csrf_storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME, secret_phrase="test")

    app = web.Application()

    aiohttp_csrf.setup(app, policy=csrf_policy, storage=csrf_storage)

    app.middlewares.append(aiohttp_csrf.csrf_middleware)

    async def handler_get_form_with_post_token(request):
        token = await aiohttp_csrf.generate_token(request)

        body = """
            <html>
                <head><title>Form with csrf protection</title></head>
                <body>
                    <form method="POST" action="/post_with_check">
                        <input type="hidden" name="{field_name}" value="{token}" />
                        <input type="text" name="name" />
                        <input type="submit" value="Say hello">
                    </form>
                </body>
            </html>
        """  # noqa

        body = body.format(field_name=FORM_FIELD_NAME, token=token)

        return web.Response(
            body=body.encode("utf-8"),
            content_type="text/html",
        )

    async def handler_get_form_with_get_token(request):
        token = await aiohttp_csrf.generate_token(request)

        body = """
            <html>
                <head><title>Form with csrf protection</title></head>
                <body>
                    <form method="POST" action="/post_with_check/{token}">
                        <input type="text" name="name" />
                        <input type="submit" value="Say hello">
                    </form>
                </body>
            </html>
        """  # noqa

        body = body.format(field_name=FORM_FIELD_NAME, token=token)

        return web.Response(
            body=body.encode("utf-8"),
            content_type="text/html",
        )

    async def handler_post_check(request):
        post = await request.post()

        body = "Hello, {name}".format(name=post["name"])

        return web.Response(
            body=body.encode("utf-8"),
            content_type="text/html",
        )

    async def handler_get_form_without_token(request):
        body = """
            <html>
                <head><title>Form without csrf protection</title></head>
                <body>
                    <form method="POST" action="/post_without_check">
                        <input type="text" name="name" />
                        <input type="submit" value="Say hello">
                    </form>
                </body>
            </html>
        """

        return web.Response(
            body=body.encode("utf-8"),
            content_type="text/html",
        )

    @aiohttp_csrf.csrf_exempt
    async def handler_post_not_check(request):
        post = await request.post()

        body = "Hello, {name}".format(name=post["name"])

        return web.Response(
            body=body.encode("utf-8"),
            content_type="text/html",
        )

    async def handler_index(request):
        body = """
            <html>
                <head><title>Forms</title></head>
                <body>
                    <ul>
                    <li><a href="/form_with_post_check">form with token field</a></li>
                    <li><a href="/form_with_get_check">form with token URL</a></li>
                    <li><a href="/form_without_check">form without checks</a></li>
                    </ul>
                </body>
            </html>
        """

        return web.Response(
            body=body.encode("utf-8"),
            content_type="text/html",
        )

    app.router.add_route(
        "GET",
        "/",
        handler_index,
    )
    app.router.add_route(
        "GET",
        "/form_with_post_check",
        handler_get_form_with_post_token,
    )
    app.router.add_route(
        "GET",
        "/form_with_get_check",
        handler_get_form_with_get_token,
    )
    app.router.add_route(
        "POST",
        "/post_with_check/{" + FORM_FIELD_NAME + "}",
        handler_post_check,
    )
    app.router.add_route(
        "POST",
        "/post_with_check",
        handler_post_check,
    )
    app.router.add_route(
        "GET",
        "/form_without_check",
        handler_get_form_without_token,
    )
    app.router.add_route(
        "POST",
        "/post_without_check",
        handler_post_not_check,
    )

    return app


web.run_app(make_app())
