from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from database import get_session
from limiter import AUTH_RATE_LIMIT, limiter
from models.schemas import TokenResponse
from security.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/token",
    response_model=TokenResponse,
    responses={
        401: {"description": "Usuário ou senha incorretos"},
        429: {"description": "Muitas tentativas de login. Tente novamente mais tarde."},
    },
)
@limiter.limit(AUTH_RATE_LIMIT)  # anti brute force: 10 req/min por cliente
def login(
    request: Request,  # exigido pelo SlowAPI
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    if not authenticate_user(session, form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=token)
