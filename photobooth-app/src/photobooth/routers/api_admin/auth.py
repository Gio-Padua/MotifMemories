import logging
import time
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from ..auth_dependencies_bearer import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_users,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["admin", "auth"])
_failed_logins: dict[str, list[float]] = {}


@router.post("/token")
async def login_for_access_token(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    key = request.client.host if request.client else "local"
    now = time.monotonic()
    failures = [attempt for attempt in _failed_logins.get(key, []) if now - attempt < 300]
    if len(failures) >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed attempts. Try again in five minutes.")
    user = authenticate_user(get_users(), form_data.username, form_data.password)
    if not user:
        _failed_logins[key] = [*failures, now]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _failed_logins.pop(key, None)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user
