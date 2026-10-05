"""Middleware de segurança HTTP para aplicação de cabeçalhos OWASP Top 10."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware para injeção de headers HTTP de segurança (OWASP Top 10):
    - Strict-Transport-Security (HSTS): força uso estrito de conexões HTTPS.
    - X-Frame-Options: mitiga ataques de Clickjacking impedindo que a aplicação seja renderizada em frames/iframes.
    - X-Content-Type-Options: mitiga MIME-sniffing forçando o navegador a respeitar o Content-Type declarado.
    - Content-Security-Policy (CSP): mitiga Cross-Site Scripting (XSS) e injeção de dados definindo origens confiáveis.
    - X-XSS-Protection: proteção legada para bloqueio de XSS refletido em navegadores compatíveis.
    - Referrer-Policy: controla quais informações de referência são enviadas ao navegar para outros domínios.
    - Permissions-Policy: restringe acesso a APIs sensíveis do navegador (câmera, microfone, geolocalização).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # HSTS (Strict-Transport-Security)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Anti-Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Anti-MIME-Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Content-Security-Policy (CSP) - permite Swagger UI (/docs) via cdn.jsdelivr.net
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self'"
        )

        # Headers adicionais de hardening
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=()"
        )

        return response
