import logging

from fastapi import APIRouter, Header, HTTPException

from ...container import container
from ...services.processing import ActionType
from ...utils.exceptions import ProcessMachineOccupiedError
from ...services.kiosk_payment import KioskPaymentRequiredError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/{action_type}/{index}")
def api_trigger_model(action_type: ActionType, index: int = 0, x_kiosk_test_grant: str | None = Header(default=None)):
    try:
        container.processing_service.trigger_action(action_type, index, x_kiosk_test_grant)

    except ProcessMachineOccupiedError as exc:
        # raised if processingservice not idle
        raise HTTPException(status_code=400, detail=f"only one capture at a time allowed: {exc}") from exc
    except KioskPaymentRequiredError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        # other errors
        logger.critical(exc, exc_info=exc)
        raise HTTPException(status_code=500, detail=f"something went wrong, Exception: {exc}") from exc
