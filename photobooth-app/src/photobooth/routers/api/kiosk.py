from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response, status

from ...container import container
from ...services.kiosk_payment import KioskPaymentRequiredError

router = APIRouter(prefix="/kiosk", tags=["kiosk"])


@router.get("/status")
def kiosk_status(x_kiosk_test_grant: str | None = Header(default=None)):
    return container.kiosk_payment_service.status(x_kiosk_test_grant)


@router.post("/session/done")
def kiosk_done():
    container.kiosk_payment_service.done()


@router.post("/results/{media_id}/print")
def kiosk_print(media_id: UUID, action_index: int, x_kiosk_test_grant: str | None = Header(default=None)):
    try:
        container.kiosk_payment_service.print_result(media_id, action_index, x_kiosk_test_grant)
    except KioskPaymentRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/results/{media_id}/download")
def kiosk_download(media_id: UUID, response: Response):
    result = container.kiosk_payment_service.download_status(media_id)
    if result.get("status") in ("queued", "uploading"):
        response.status_code = status.HTTP_202_ACCEPTED
        response.headers["Retry-After"] = "2"
    elif result.get("status") != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
