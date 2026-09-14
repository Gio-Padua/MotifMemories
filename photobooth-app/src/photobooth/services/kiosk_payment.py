import logging
import shutil
from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..appconfig import appconfig
from ..database.database import engine
from ..database.models import KioskPaymentSession, Mediaitem
from ..plugins import pm as pluggy_pm
from ..utils.printer import PrinterStatus, get_printer_status
from .acquisition import AcquisitionService
from .base import BaseService
from .collection import MediacollectionService
from .kiosk_credit import apply_bill, partial_credit_expired
from .kiosk_filters import FILTERS, render_look
from .share import ShareService
from .sse import sse_service
from .sse.sse_ import SseEventKioskState

logger = logging.getLogger(__name__)
ACTIVE_STATES = ("collecting", "paid", "capturing", "presenting")


class KioskPaymentRequiredError(PermissionError):
    pass


class KioskResultNotFoundError(FileNotFoundError):
    pass


class KioskPaymentService(BaseService):
    """Single-terminal payment ledger. Hardware calls accept_bill after qualification."""

    def __init__(self, acquisition: AcquisitionService, collection: MediacollectionService, share: ShareService):
        super().__init__()
        self._acquisition = acquisition
        self._collection = collection
        self._share = share
        self._lock = Lock()
        self._render_lock = Lock()
        self._last_cleanup = datetime.min

    def start(self):
        super().start()
        self._recover_interrupted_capture()
        with Session(engine) as db:
            item = self._active(db)
            recovery = (
                (item.id, UUID(item.printable_result_id), item.selected_filter)
                if item and item.presentation_stage == "rendering" and item.printable_result_id
                else None
            )
        if recovery:
            try:
                self._finish_render(*recovery)
            except Exception:
                logger.exception("Could not recover kiosk filter render; original is retained")
        super().started()

    def stop(self):
        super().stop()
        super().stopped()

    @staticmethod
    def is_protected(action_name: str) -> bool:
        return action_name in appconfig.kiosk.protected_action_names

    def _active(self, session: Session) -> KioskPaymentSession | None:
        return session.scalars(
            select(KioskPaymentSession).where(KioskPaymentSession.state.in_(ACTIVE_STATES)).order_by(KioskPaymentSession.id.desc()).limit(1)
        ).one_or_none()

    def _recover_interrupted_capture(self):
        with Session(engine) as db:
            item = self._active(db)
            if item and item.state == "capturing":
                item.state = "presenting" if item.result_ids else "paid"
                item.reserved_retake = False
                db.commit()

    def _readiness(self, test_mode: bool = False) -> dict[str, bool]:
        camera = self._acquisition.is_running()
        printer = False
        for action in appconfig.share.actions:
            if not (action.handles_images_only and action.trigger.ui_trigger.show_button and not action.processing.ask_user_for_parameter_input):
                continue
            if not action.processing.check_if_printer_is_idle:
                printer = True
                break
            try:
                printer = get_printer_status(action.processing.printer_name)[0] is PrinterStatus.OK
            except Exception:
                printer = False
            break

        disk = shutil.disk_usage(".").free >= appconfig.kiosk.minimum_free_disk_gib * 1024**3
        cloud_results = pluggy_pm.hook.kiosk_storage_health()
        cloud = any(value is True for value in cloud_results)
        password = appconfig.common.admin_password.get_secret_value() != "0000"
        validator = False  # No credit path until the purchased TB74 interface is qualified.
        return {
            "camera": camera,
            "printer": printer,
            "disk": disk,
            "cloud": cloud,
            "payment_hardware": validator,
            "password_changed": password,
            "ready": camera if test_mode else all((camera, printer, disk, cloud, validator, password, appconfig.kiosk.payment_enabled)),
        }

    def status(self, test_grant: str | None = None) -> dict:
        self._run_retention_if_due()
        with self._lock, Session(engine) as db:
            item = self._active(db)
            now = datetime.now()
            if item and item.state == "collecting" and partial_credit_expired(item.deadline, now):
                item.state = "forfeited"
                item.completed_at = now
                db.commit()
                item = None

            grant_valid = bool(test_grant and self.validate_test_grant(test_grant))
            test_mode = bool(item and item.mode == "test" and grant_valid)
            readiness = self._readiness(test_mode=test_mode)
            remaining = max((item.deadline - now).total_seconds(), 0) if item and item.deadline else None
            result = {
                "payment_enabled": appconfig.kiosk.payment_enabled,
                "price": appconfig.kiosk.price_php,
                "denominations": appconfig.kiosk.accepted_denominations_php,
                "readiness": readiness,
                "test_grant_valid": grant_valid,
                "storage": next(iter(pluggy_pm.hook.kiosk_storage_diagnostics()), {"configured": False, "message": "Storage plugin unavailable"}),
                "session": None,
            }
            if item:
                result["session"] = {
                    "id": item.id,
                    "mode": item.mode,
                    "state": item.state,
                    "credit": item.credited_amount,
                    "remaining_balance": max(item.price - item.credited_amount, 0),
                    "overpayment": item.overpayment,
                    "seconds_remaining": round(remaining) if remaining is not None else None,
                    "result_ids": item.result_ids,
                    "retakes_remaining": max(appconfig.kiosk.free_retakes - item.retakes_used, 0) if item.prints_used == 0 else 0,
                    "prints_remaining": max(appconfig.kiosk.included_prints - item.prints_used, 0),
                    "printable_result_id": item.printable_result_id,
                    "presentation_stage": item.presentation_stage,
                    "selected_filter": item.selected_filter,
                }
                if item.presentation_stage != "review":
                    result["session"]["retakes_remaining"] = 0
                if item.printable_result_id:
                    media = db.get(Mediaitem, UUID(item.printable_result_id))
                    result["session"]["upload"] = media.customer_delivery if media else None
            return result

    def _run_retention_if_due(self):
        now = datetime.now()
        if now - self._last_cleanup < timedelta(hours=1):
            return
        self._last_cleanup = now
        cutoff = now - timedelta(days=appconfig.kiosk.retention_days)
        with Session(engine) as db:
            old_sessions = list(db.scalars(select(KioskPaymentSession).where(KioskPaymentSession.created_at < cutoff)).all())
            old_session_ids = [session.id for session in old_sessions]
            kiosk_result_ids = {value for session in old_sessions for value in session.result_ids}
        for value in kiosk_result_ids:
            try:
                pluggy_pm.hook.collection_customer_result_deleted(identifier=UUID(value))
            except Exception as exc:
                logger.warning(f"cloud retention cleanup failed for {value}: {exc}")
            try:
                media = self._collection.get_item(UUID(value))
                for related in self._collection.get_items_relto_job(media.job_identifier):
                    self._collection.delete_item(related, delete_to_recycle_dir=False)
            except (FileNotFoundError, ValueError):
                continue
            except Exception as exc:
                logger.warning(f"kiosk retention cleanup failed for {value}: {exc}")
        with Session(engine) as db:
            for session_id in old_session_ids:
                if item := db.get(KioskPaymentSession, session_id):
                    db.delete(item)
            db.commit()

    def emit(self):
        sse_service.dispatch_event(SseEventKioskState(state=self.status()))

    def initial_emit(self):
        self.emit()

    def accept_bill(self, denomination: int) -> dict:
        with self._lock, Session(engine) as db:
            item = self._active(db)
            if not item:
                if not self._readiness()["ready"]:
                    raise KioskPaymentRequiredError("booth is not ready to accept payment")
                item = KioskPaymentSession(
                    mode="paid",
                    state="collecting",
                    price=appconfig.kiosk.price_php,
                    inserted_bills=[],
                    credited_amount=0,
                    overpayment=0,
                    deadline=datetime.now() + timedelta(seconds=appconfig.kiosk.partial_credit_timeout_seconds),
                    result_ids=[],
                    retakes_used=0,
                    prints_used=0,
                    reserved_retake=False,
                )
                db.add(item)
            if item.mode != "paid" or item.state != "collecting":
                raise KioskPaymentRequiredError("validator is inhibited")
            bills, credit, overpayment, paid = apply_bill(item.inserted_bills, denomination, item.price, appconfig.kiosk.accepted_denominations_php)
            item.inserted_bills = bills
            item.credited_amount = credit
            item.overpayment = overpayment
            if paid:
                item.state = "paid"
                item.deadline = None
            db.commit()
        self.emit()
        return self.status()

    def create_test_grant(self) -> str:
        now = datetime.now(UTC)
        token = jwt.encode(
            {"sub": "admin", "scope": "kiosk-test", "iat": now, "exp": now + timedelta(hours=4)},
            appconfig.misc.secret,
            algorithm="HS256",
        )
        with self._lock, Session(engine) as db:
            active = self._active(db)
            if active:
                if active.state == "capturing" or active.presentation_stage == "rendering":
                    raise KioskPaymentRequiredError("Wait for the current capture or filter to finish")
                active.state = "voided"
                active.completed_at = datetime.now()
            db.add(
                KioskPaymentSession(
                    mode="test",
                    state="paid",
                    price=0,
                    inserted_bills=[],
                    credited_amount=0,
                    overpayment=0,
                    result_ids=[],
                    retakes_used=0,
                    prints_used=0,
                    reserved_retake=False,
                )
            )
            db.commit()
        self.emit()
        return token

    @staticmethod
    def validate_test_grant(token: str) -> bool:
        try:
            payload = jwt.decode(token, appconfig.misc.secret, algorithms=["HS256"])
            return payload.get("sub") == "admin" and payload.get("scope") == "kiosk-test"
        except InvalidTokenError:
            return False

    def reserve_capture(self, action_name: str, test_grant: str | None):
        if not self.is_protected(action_name):
            return
        with self._lock, Session(engine) as db:
            item = self._active(db)
            if not item:
                raise KioskPaymentRequiredError("payment or operator test grant required")
            if item.mode == "test" and not (test_grant and self.validate_test_grant(test_grant)):
                raise KioskPaymentRequiredError("valid operator test grant required")
            if item.mode == "paid" and not self._readiness()["ready"]:
                raise KioskPaymentRequiredError("paid credit is safe; booth readiness must recover before capture")
            if item.state == "paid":
                item.reserved_retake = False
            elif (
                item.state == "presenting"
                and item.presentation_stage == "review"
                and item.prints_used == 0
                and item.retakes_used < appconfig.kiosk.free_retakes
            ):
                item.reserved_retake = True
            else:
                raise KioskPaymentRequiredError("capture entitlement is not available")
            item.state = "capturing"
            db.commit()
        self.emit()

    def release_capture(self):
        with self._lock, Session(engine) as db:
            item = self._active(db)
            if item and item.state == "capturing":
                item.state = "presenting" if item.result_ids else "paid"
                item.reserved_retake = False
                db.commit()
        self.emit()

    def complete_capture(self, media_id: UUID):
        with self._lock, Session(engine) as db:
            item = self._active(db)
            if not item or item.state != "capturing":
                return
            result_id = str(media_id)
            item.result_ids = [*item.result_ids, result_id]
            if item.reserved_retake:
                item.retakes_used += 1
            item.printable_result_id = result_id
            item.reserved_retake = False
            item.state = "presenting"
            item.presentation_stage = "review"
            item.selected_filter = "original"
            db.commit()
        self.emit()

    def is_kiosk_result(self, media_id: UUID) -> bool:
        with Session(engine) as db:
            return any(str(media_id) in item.result_ids for item in db.scalars(select(KioskPaymentSession)))

    def _current_result(self, db: Session, media_id: UUID, test_grant: str | None):
        item = self._active(db)
        if not item or item.state != "presenting" or item.printable_result_id != str(media_id):
            raise KioskPaymentRequiredError("This is not the current kiosk result")
        if item.mode == "test" and not (test_grant and self.validate_test_grant(test_grant)):
            raise KioskPaymentRequiredError("Valid operator test grant required")
        return item

    def keep_result(self, media_id: UUID, test_grant: str | None):
        with self._lock, Session(engine) as db:
            item = self._current_result(db, media_id, test_grant)
            if item.presentation_stage == "review":
                item.presentation_stage = "filters"
                db.commit()
        self.emit()

    def finalize_result(self, media_id: UUID, look: str, test_grant: str | None):
        if look not in FILTERS:
            raise ValueError("Unknown kiosk filter")
        if not self._render_lock.acquire(blocking=False):
            raise KioskPaymentRequiredError("A filter is already being prepared")
        try:
            with self._lock, Session(engine) as db:
                item = self._current_result(db, media_id, test_grant)
                if item.presentation_stage == "delivery" and item.selected_filter == look:
                    return self._collection.get_item(media_id)
                if item.presentation_stage != "filters":
                    raise KioskPaymentRequiredError("Keep the photos before choosing a look; delivered looks are locked")
                item.selected_filter = look
                item.presentation_stage = "rendering"
                session_id = item.id
                db.commit()
            self.emit()
            return self._finish_render(session_id, media_id, look)
        finally:
            self._render_lock.release()

    def _finish_render(self, session_id: int, media_id: UUID, look: str):
        try:
            mediaitem = self._collection.get_item(media_id)
            render_look(mediaitem, look)
            mediaitem.pipeline_config = {**mediaitem.pipeline_config, "kiosk_filter": look}
            self._collection.update_item(mediaitem)
            with self._lock, Session(engine) as db:
                item = db.get(KioskPaymentSession, session_id)
                item.presentation_stage = "delivery"
                media = db.get(Mediaitem, media_id)
                media.customer_delivery = {"status": "queued", "attempts": 0}
                db.commit()
        except Exception:
            with Session(engine) as db:
                item = db.get(KioskPaymentSession, session_id)
                if item:
                    item.presentation_stage = "filters"
                    db.commit()
            self.emit()
            raise
        try:
            pluggy_pm.hook.collection_customer_result_added(filepath_local=mediaitem.processed, identifier=media_id)
        except Exception:
            logger.exception("Customer delivery queue failed; final image remains local")
        self.emit()
        return self._collection.get_item(media_id)

    def print_result(self, media_id: UUID, action_index: int, test_grant: str | None = None):
        try:
            if action_index < 0:
                raise IndexError
            action = appconfig.share.actions[action_index]
        except IndexError as exc:
            raise ValueError("invalid print action") from exc
        if not (action.handles_images_only and action.trigger.ui_trigger.show_button and not action.processing.ask_user_for_parameter_input):
            raise ValueError("action is not an enabled parameter-free image print action")
        with self._lock, Session(engine) as db:
            item = self._active(db)
            if not item or item.state != "presenting" or item.presentation_stage != "delivery" or item.printable_result_id != str(media_id):
                raise KioskPaymentRequiredError("this result is not printable")
            if item.mode == "test" and not (test_grant and self.validate_test_grant(test_grant)):
                raise KioskPaymentRequiredError("valid operator test grant required")
            if item.prints_used >= appconfig.kiosk.included_prints:
                raise KioskPaymentRequiredError("included print already used")
            mediaitem = self._collection.get_item(media_id)
            self._share.share(mediaitem, action_index)
            item.prints_used += 1
            db.commit()
        self.emit()

    def done(self):
        with self._lock, Session(engine) as db:
            item = self._active(db)
            if item:
                if item.presentation_stage == "rendering":
                    raise KioskPaymentRequiredError("Please wait for the image to finish")
                item.state = "completed"
                item.completed_at = datetime.now()
                db.commit()
        self.emit()

    def void(self):
        with self._lock, Session(engine) as db:
            item = self._active(db)
            if item:
                if item.presentation_stage == "rendering":
                    raise KioskPaymentRequiredError("Please wait for the image to finish")
                item.state = "voided"
                item.completed_at = datetime.now()
                db.commit()
        self.emit()

    def download_status(self, media_id: UUID) -> dict:
        with Session(engine) as db:
            # ponytail: one-terminal seven-day ledger; normalize result IDs only if lookup volume grows.
            recorded = any(str(media_id) in item.result_ids for item in db.scalars(select(KioskPaymentSession)).all())
        if not recorded:
            raise KioskResultNotFoundError(str(media_id))
        mediaitem = self._collection.get_item(media_id)
        if mediaitem.filter_source and not mediaitem.customer_delivery:
            raise KioskPaymentRequiredError("Confirm the photos and filter before downloading")

        results = pluggy_pm.hook.get_customer_result_status(identifier=media_id)
        for result in results:
            if result:
                return result

        try:
            mediaitem = self._collection.get_item(media_id)
            pluggy_pm.hook.collection_customer_result_added(filepath_local=mediaitem.processed, identifier=media_id)
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}

        for result in pluggy_pm.hook.get_customer_result_status(identifier=media_id):
            if result:
                return result
        return {"status": "failed", "error": "customer storage is not configured"}

    def retry_download(self, media_id: UUID, test_grant: str | None):
        with self._lock, Session(engine) as db:
            item = self._current_result(db, media_id, test_grant)
            if item.presentation_stage != "delivery":
                raise KioskPaymentRequiredError("Confirm this result first")
        pluggy_pm.hook.kiosk_retry_customer_result(identifier=media_id)
