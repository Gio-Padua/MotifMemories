from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...container import container
from ...services.kiosk_payment import KioskPaymentRequiredError
from ..auth_dependencies_bearer import User, get_current_active_user

router = APIRouter(prefix="/kiosk", tags=["admin", "kiosk"])


@router.post("/test-grant")
def create_test_grant(_: Annotated[User, Depends(get_current_active_user)]):
    try:
        return {"grant": container.kiosk_payment_service.create_test_grant(), "expires_in": 4 * 60 * 60}
    except KioskPaymentRequiredError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/session/void")
def void_session(_: Annotated[User, Depends(get_current_active_user)]):
    try:
        container.kiosk_payment_service.void()
    except KioskPaymentRequiredError as exc:
        raise HTTPException(409, str(exc)) from exc
