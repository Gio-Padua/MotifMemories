from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...container import container
from ...services.config.groups.actions import CollageProcessing
from ...services.kiosk_filters import FILTERS, compose_look
from ...services.kiosk_payment import KioskPaymentRequiredError, KioskResultNotFoundError

router = APIRouter(prefix="/kiosk", tags=["kiosk"])
preview_lock = Lock()


@router.get("/status")
def kiosk_status(x_kiosk_test_grant: str | None = Header(default=None)):
    return container.kiosk_payment_service.status(x_kiosk_test_grant)


@router.post("/session/done")
def kiosk_done():
    try:
        container.kiosk_payment_service.done()
    except KioskPaymentRequiredError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/results/{media_id}/keep")
def kiosk_keep(media_id: UUID, x_kiosk_test_grant: str | None = Header(default=None)):
    try:
        container.kiosk_payment_service.keep_result(media_id, x_kiosk_test_grant)
        return container.kiosk_payment_service.status(x_kiosk_test_grant)
    except KioskPaymentRequiredError as exc:
        raise HTTPException(409, str(exc)) from exc


def filter_media(media_id: UUID):
    if not container.kiosk_payment_service.is_kiosk_result(media_id):
        raise HTTPException(404, "Not a kiosk result")
    return container.mediacollection_service.get_item(media_id)


@router.get("/results/{media_id}/filters")
def kiosk_filters(media_id: UUID):
    media = filter_media(media_id)
    return [
        {"id": key, "label": key.title(), "preview_url": f"/api/kiosk/results/{media_id}/filters/{key}/preview"}
        for key in FILTERS
        if media.filter_source or key == "original"
    ]


@router.get("/results/{media_id}/filters/{filter_id}/preview")
def kiosk_filter_preview(media_id: UUID, filter_id: Literal["original", "soft", "warm", "mono"]):
    media = filter_media(media_id)
    if not media.filter_source:
        if filter_id == "original":
            return FileResponse(media.processed, media_type="image/jpeg")
        raise HTTPException(409, "Filter source unavailable")
    path = Path("cache", f"kiosk-filter-{media_id}-{filter_id}.jpg")
    with preview_lock:
        if not path.exists():
            from uuid import uuid4

            temporary = path.with_name(f"{path.stem}-{uuid4()}.tmp")
            try:
                image = compose_look(media.filter_source, CollageProcessing(**media.pipeline_config), filter_id, preview=True)
                image.save(temporary, format="JPEG", quality=85)
                image.close()
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})


class FinalizeLook(BaseModel):
    filter: Literal["original", "soft", "warm", "mono"]


@router.post("/results/{media_id}/download/retry")
def kiosk_retry_download(media_id: UUID, x_kiosk_test_grant: str | None = Header(default=None)):
    try:
        container.kiosk_payment_service.retry_download(media_id, x_kiosk_test_grant)
    except KioskPaymentRequiredError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/results/{media_id}/finalize")
def kiosk_finalize(media_id: UUID, body: FinalizeLook, x_kiosk_test_grant: str | None = Header(default=None)):
    try:
        media = container.kiosk_payment_service.finalize_result(media_id, body.filter, x_kiosk_test_grant)
        return {"id": str(media.id), "revision": media.revision}
    except KioskPaymentRequiredError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, "Could not prepare this look. Retry or use Original.") from exc


@router.post("/results/{media_id}/print")
def kiosk_print(media_id: UUID, action_index: int, x_kiosk_test_grant: str | None = Header(default=None)):
    try:
        container.kiosk_payment_service.print_result(media_id, action_index, x_kiosk_test_grant)
    except KioskPaymentRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/results/{media_id}/download")
def kiosk_download(media_id: UUID, response: Response):
    try:
        result = container.kiosk_payment_service.download_status(media_id)
    except KioskResultNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="result is not part of a kiosk session") from exc
    except KioskPaymentRequiredError as exc:
        raise HTTPException(409, str(exc)) from exc
    if result.get("status") in ("queued", "uploading"):
        response.status_code = status.HTTP_202_ACCEPTED
        response.headers["Retry-After"] = "2"
    elif result.get("status") != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
