from typing import Annotated

from fastapi import APIRouter, Depends

from ...container import container
from ..auth_dependencies_bearer import User, get_current_active_user

router = APIRouter(prefix="/kiosk", tags=["admin", "kiosk"])


@router.post("/test-grant")
def create_test_grant(_: Annotated[User, Depends(get_current_active_user)]):
    return {"grant": container.kiosk_payment_service.create_test_grant(), "expires_in": 4 * 60 * 60}


@router.post("/session/void")
def void_session(_: Annotated[User, Depends(get_current_active_user)]):
    container.kiosk_payment_service.void()
