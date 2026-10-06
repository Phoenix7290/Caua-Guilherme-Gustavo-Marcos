import os

from slowapi import Limiter
from starlette.requests import Request

# Atrás do Cloudflare Tunnel o IP de origem vem em CF-Connecting-IP.
# Só confie nesse header se a API NÃO for acessível direto (senão dá pra forjar).
TRUST_CF_HEADER = os.getenv("TRUST_CF_HEADER", "false").lower() == "true"


def client_key(request: Request) -> str:
    if TRUST_CF_HEADER:
        ip = request.headers.get("cf-connecting-ip")
        if ip:
            return ip.strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_key)

AUTH_RATE_LIMIT = "10/minute"
