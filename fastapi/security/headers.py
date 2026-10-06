import base64
import hashlib
import re

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

# CSP padrão para as respostas JSON da API: nada pode ser carregado/embutido.
API_CSP = "default-src 'none'; frame-ancestors 'none'"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",  # anti-clickjacking
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def _sha256(content: str) -> str:
    return "'sha256-" + base64.b64encode(hashlib.sha256(content.encode()).digest()).decode() + "'"


def install_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        response.headers.setdefault("Content-Security-Policy", API_CSP)
        return response


def install_docs(app: FastAPI) -> None:
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=None,
    ).body.decode()
    inline = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    csp = "; ".join([
        "default-src 'none'",
        f"script-src {_sha256(inline)} https://cdn.jsdelivr.net",
        "style-src https://cdn.jsdelivr.net",
        "img-src 'self' data: https://fastapi.tiangolo.com",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'none'",
        "form-action 'none'",
    ])

    @app.get("/docs", include_in_schema=False)
    def swagger_docs():
        return HTMLResponse(html, headers={"Content-Security-Policy": csp})
