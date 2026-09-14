import configparser
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import resources
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic
from urllib.parse import quote
from uuid import UUID

import requests
from PIL import Image
from rclone_api.api import RcloneApi
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ...database.database import engine
from ...database.models import Mediaitem
from ...models.genericstats import GenericStats, SubList, SubStats
from .. import hookimpl
from ..base_plugin import BasePlugin
from .config import RemoteConfig, SynchronizerConfig
from .immediate_synchronizer import ThreadedImmediateSyncPipeline
from .regular_synchronizer import ThreadedRegularSync
from .shareondemand import ShareOnDemandService
from .types import TaskCopy, TaskDelete
from .utils import get_corresponding_remote_file

logger = logging.getLogger(__name__)


@dataclass
class CustomerResultTransfer:
    jobid: int | None
    remote: RemoteConfig
    destination: str
    url: str
    error: str | None = None
    attempts: int = 0
    retry_at: float = 0
    ready: bool = False
    failures: int = 0


class Synchronizer(BasePlugin[SynchronizerConfig]):
    def __init__(self):
        super().__init__()
        self._config = SynchronizerConfig()

        self._rclone_client: RcloneApi | None = None

        self._immediate_pipeline: ThreadedImmediateSyncPipeline | None = None
        self._regular_sync: ThreadedRegularSync | None = None
        self._shareondemand: ShareOnDemandService | None = None
        self._customer_remote: RemoteConfig | None = None
        self._customer_results: dict[UUID, CustomerResultTransfer] = {}
        self._customer_lock = Lock()
        self._storage_health: tuple[datetime, bool] | None = None
        self._storage_error = "Synchronizer is disabled"
        self._customer_stop = Event()
        self._customer_thread: Thread | None = None

    def __str__(self):
        return "Sync and Share Online"

    @hookimpl
    def start(self):
        if not self._config.common.enabled:
            logger.info("Synchronizer Plugin is disabled")
            return

        # _bind_gui = "0.0.0.0:5573" if self._config.rclone_config.webui_allow_remote_access else "127.0.0.1:5573"
        _bind_gui = "127.0.0.1:5573"
        _log_file = Path("log/rclone.log") if self._config.rclone_config.rclone_enable_logging else None
        _config_file = Path("./config/rclone.conf")
        logger.info("Rclone configuration: %s", _config_file.resolve())
        _immediate_sync_remotes = [x for x in self._config.remotes if x.enable_immediate_sync and x.enabled and x.sync_scope == "archive"]
        _full_sync_remotes = [x for x in self._config.remotes if x.enable_regular_sync and x.enabled and x.sync_scope == "archive"]
        _copy_sharepage_to_remotes = [x for x in self._config.remotes if x.enabled and x.enable_sharepage_sync and x.enabled]
        customer_remotes = [x for x in self._config.remotes if x.enabled and x.enable_immediate_sync and x.sync_scope == "customer_results"]
        self._customer_remote = customer_remotes[0] if customer_remotes else None
        if len(customer_remotes) > 1:
            logger.warning("only the first customer_results remote is used")

        if self._customer_remote:
            settings = configparser.ConfigParser(interpolation=None)
            settings.read(_config_file)
            name = self._customer_remote.name.rstrip(":")
            if not settings.has_section(name):
                self._storage_error = "Runtime rclone.conf or the configured remote is missing"
                logger.error(self._storage_error)
                return
        self._storage_error = "Customer-results remote is missing" if not self._customer_remote else "Storage has not been checked yet"

        self._rclone_client = RcloneApi(
            bind_gui=_bind_gui,
            log_file=_log_file,
            log_level=self._config.rclone_config.rclone_log_level,
            transfers=self._config.rclone_config.rclone_transfers,
            checkers=self._config.rclone_config.rclone_checkers,
            enable_webui=self._config.rclone_config.enable_webui,
            config_file=_config_file,
            # bwlimit="1M",
        )
        self._rclone_client.start()
        if self._customer_remote:
            self._customer_stop.clear()
            self._customer_thread = Thread(target=self._customer_worker, name="kiosk-delivery", daemon=True)
            self._customer_thread.start()

        self._regular_sync = ThreadedRegularSync(
            rclone=self._rclone_client,
            fullsync_remotes=_full_sync_remotes,
            sync_interval_s=60 * self._config.common.full_sync_interval,
            usb_drive_change_monitor=self._config.common.usb_drive_change_monitor,
        )
        self._immediate_pipeline = ThreadedImmediateSyncPipeline(
            rclone=self._rclone_client,
            remotes=_immediate_sync_remotes,
        )

        if self._config.ondemandshareconfig.enabled:
            self._shareondemand = ShareOnDemandService(
                rclone=self._rclone_client,
                remote_name=self._config.ondemandshareconfig.name,
                remote_subdir=self._config.ondemandshareconfig.subdir,
                baseurl=self._config.ondemandshareconfig.baseurl,
                apikey=self._config.ondemandshareconfig.apikey,
            )

            self._shareondemand.start()

        for r in _copy_sharepage_to_remotes:
            self._copy_sharepage_to_remotes(r)

    @hookimpl
    def stop(self):

        self._customer_stop.set()
        if self._customer_thread:
            self._customer_thread.join(timeout=15)

        if self._regular_sync:
            self._regular_sync.stop()

        if self._immediate_pipeline:
            self._immediate_pipeline.stop()

        if self._shareondemand:
            self._shareondemand.stop()

        if self._rclone_client:
            self._rclone_client.stop()

    def wait_until_ready(self, timeout: float = 5) -> None:
        if not self._rclone_client:
            raise RuntimeError("cannot wait for the service to be ready if not enabled and started before!")

        if self._rclone_client:
            self._rclone_client.wait_until_operational(timeout)

    @hookimpl
    def get_stats(self) -> GenericStats | None:
        if self._config.common.enabled is False:
            # avoids display of an empty stats object in the admin dashboard
            return None
        if not (self._rclone_client and self._immediate_pipeline and self._regular_sync):
            return None

        try:
            core_stats = self._rclone_client.core_stats()
            job_list = self._rclone_client.job_list()
            immediate_stats = self._immediate_pipeline.get_stats()
            regular_stats = self._regular_sync.get_stats()
        except Exception as exc:
            return GenericStats(id="hook-plugin-synchronizer", name="Synchronizer", stats=[SubStats("Error", f"Cannot gather stats, reason: {exc}")])

        out = GenericStats(id="hook-plugin-synchronizer", name="Synchronizer")

        out.stats.append(
            SubList(
                name="Rclone Core Stats",
                val=[
                    SubStats(
                        "Amount Finished", (float(core_stats.bytes) / float(core_stats.totalBytes) * 100.0) if core_stats.totalBytes else 0, unit="%"
                    ),
                    SubStats("Amount", core_stats.bytes / 1024 / 1024, unit="Mb"),
                    SubStats("Total Amount", core_stats.totalBytes / 1024 / 1024, unit="Mb"),
                    SubStats("eta", core_stats.eta, unit="s"),
                    SubStats("errors", core_stats.errors),
                    SubStats("speed", core_stats.speed / 1014 / 1014, decimals=1, unit="Mb/s"),
                    SubStats("totalTransfers", core_stats.totalTransfers),
                    SubStats("deletes", core_stats.deletes),
                ],
            )
        )
        out.stats.append(SubStats("lastError", core_stats.lastError))

        out.stats.append(
            SubList(
                name="Immediate Sync Stats (#files since app start)",
                val=[
                    SubStats("Pending", immediate_stats.pending),
                    SubStats("Transferring", immediate_stats.transferring),
                    SubStats("Finished", immediate_stats.finished),
                    SubStats("Failed", immediate_stats.failed),
                    SubStats("Total", immediate_stats.total),
                ],
            )
        )
        out.stats.append(
            SubList(
                name="Regular Full Sync Stats",
                val=[
                    SubStats(
                        "last_check_started",
                        regular_stats.last_check_started.astimezone().strftime("%X") if regular_stats.last_check_started else None,
                    ),
                    SubStats("next_check", regular_stats.next_check.astimezone().strftime("%X") if regular_stats.next_check else None),
                ],
            )
        )

        for idx, active_transfer in enumerate(core_stats.transferring):
            out.stats.append(
                SubList(
                    name=f"Transfer #{idx}",
                    val=[
                        SubStats("file", active_transfer.name),
                        SubStats("percentage", active_transfer.percentage, unit="%"),
                        SubStats("speedAvg", active_transfer.speedAvg / 1014 / 1014, decimals=1, unit="MB/s"),
                    ],
                )
            )

        for running_jobid in sorted(job_list.runningIds):
            job_status = self._rclone_client.job_status(running_jobid)

            if not job_status.finished:
                out.stats.append(
                    SubList(
                        name=f"Running Job #{running_jobid}",
                        val=[
                            SubStats("startTime", job_status.startTime),
                            SubStats("finished", job_status.finished),
                            SubStats("success", job_status.success),
                            SubStats("progress", job_status.progress),
                        ],
                    )
                )

        return out

    def _copy_sharepage_to_remotes(self, remote: RemoteConfig):
        assert self._rclone_client

        dlportal_source_path = Path(str(resources.files("web").joinpath("sharepage/index.html")))
        assert dlportal_source_path.is_file()

        # add to queue for later upload.
        # this way if no internet the startup is not causing issues preventing the complete app from startup
        logger.info(f"update shareportal to {remote.name}{remote.subdir}")
        self._rclone_client.copyfile_async(
            dlportal_source_path.parent.absolute().as_posix(),
            dlportal_source_path.name,
            remote.name,
            Path(remote.subdir, dlportal_source_path.name).as_posix(),
        )

    @hookimpl
    def get_share_links(self, filepath_local: Path, identifier: UUID) -> list[str]:
        if not self._rclone_client:
            return []

        share_links: list[str] = []

        if not self._config.common.enabled_share_links:
            logger.info("share link generation is disabled globally in synchronizer plugin")
            return []

        if self._config.common.enabled_custom_qr_url:
            formatted_custom_qr_url = self._config.common.custom_qr_url.format(
                filename=filepath_local.name,
                identifier=str(identifier),
            )

            share_links.append(formatted_custom_qr_url)

        if self._shareondemand:
            share_links.append(self._shareondemand.get_share_link(identifier))

        for remote in self._config.remotes:
            if remote.sync_scope == "customer_results":
                continue
            shareconfig = remote.shareconfig
            mediaitem_link: str | None = None

            if not shareconfig.enabled:
                continue

            if shareconfig.manual_public_link:
                mediaitem_link = shareconfig.manual_public_link.format(
                    filename=filepath_local.name,
                    identifier=str(identifier),
                )
            else:
                try:
                    mediaitem_link = self._rclone_client.publiclink(
                        remote.name,
                        Path(remote.subdir, get_corresponding_remote_file(filepath_local)).as_posix(),
                    ).link
                except Exception as exc:
                    logger.error(f"could not create public link due to error: {exc}")

            if not mediaitem_link:
                logger.error(
                    f"could not generate a link for {filepath_local.name} using remote {remote.name}. "
                    "If the remote does not support public links, you need to provide a manual url override or use a different provider."
                )
                continue

            # sanity check on sharepage url
            if shareconfig.use_sharepage and not shareconfig.sharepage_url:
                logger.error(
                    f"can't generate a link because the sharepage shall be used but no URL was given in the configuration for {remote.description}"
                )
                continue

            if shareconfig.use_sharepage:
                shareportal_url = f"{str(shareconfig.sharepage_url).rstrip('/')}#/?url="
                mediaitem_url_safe = quote(mediaitem_link, safe="")
                out = shareportal_url + mediaitem_url_safe
            else:
                out = mediaitem_link

            share_links.append(out)

        return share_links

    @hookimpl
    def collection_files_added(self, files: list[Path], priority_modifier: int):
        if not self._immediate_pipeline:
            return

        priority = 10 + priority_modifier
        for file in files:
            self._immediate_pipeline.submit(TaskCopy(file), priority=priority)

    @hookimpl
    def collection_files_updated(self, files: list[Path]):
        if not self._immediate_pipeline:
            return

        for file in files:
            self._immediate_pipeline.submit(TaskCopy(file), priority=15)

    @hookimpl
    def collection_files_deleted(self, files: list[Path]):
        if not self._immediate_pipeline:
            return

        for file in files:
            self._immediate_pipeline.submit(TaskDelete(file), priority=19)

    @staticmethod
    def _delivery_state(identifier: UUID) -> dict | None:
        with Session(engine) as db:
            media = db.get(Mediaitem, identifier)
            return media.customer_delivery if media else None

    @staticmethod
    def _save_delivery(identifier: UUID, value: dict):
        # Upload progress must not increment the image revision or invalidate its previews.
        with Session(engine) as db:
            db.execute(update(Mediaitem).where(Mediaitem.id == identifier).values(customer_delivery=value))
            db.commit()

    def _customer_worker(self):
        while not self._customer_stop.is_set():
            try:
                with Session(engine) as db:
                    pending = [
                        (m.id, m.processed)
                        for m in db.scalars(select(Mediaitem).where(Mediaitem.customer_delivery.is_not(None)))
                        if m.customer_delivery.get("status") in ("queued", "uploading")
                    ]
                for identifier, path in pending:
                    if self._customer_stop.is_set():
                        break
                    self.collection_customer_result_added(path, identifier)
                    self.get_customer_result_status(identifier)
            except Exception:
                logger.exception("Customer delivery worker could not advance its queue")
            self._customer_stop.wait(2)

    @hookimpl
    def collection_customer_result_added(self, filepath_local: Path, identifier: UUID) -> None:
        if not self._rclone_client or not self._customer_remote or filepath_local.suffix.lower() not in (".jpg", ".jpeg"):
            return
        with self._customer_lock:
            if identifier in self._customer_results:
                return
            state = self._delivery_state(identifier) or {"status": "queued", "attempts": 0}
            remote = self._customer_remote
            destination = Path(remote.subdir, f"{identifier}.jpg").as_posix()
            url = (remote.shareconfig.manual_public_link or "").format(filename=f"{identifier}.jpg", identifier=str(identifier))
            self._customer_results[identifier] = CustomerResultTransfer(
                None,
                remote,
                destination,
                url,
                error=state.get("error") if state.get("status") == "failed" else None,
                attempts=state.get("attempts", 0),
                failures=state.get("failures", 0),
            )
            if not self._delivery_state(identifier):
                self._save_delivery(identifier, state)

    def _advance_customer(self, identifier: UUID, transfer: CustomerResultTransfer) -> dict:
        if transfer.ready:
            return {"status": "ready", "urls": [transfer.url]}
        if transfer.error:
            return {"status": "failed", "error": transfer.error}
        if monotonic() < transfer.retry_at:
            return {"status": "queued"}
        if not transfer.url:
            raise ValueError("Public customer-result URL is not configured")
        if transfer.jobid is not None:
            try:
                job = self._rclone_client.job_status(transfer.jobid)
            except Exception as exc:
                if "job not found" not in str(exc).lower():
                    raise
                transfer.jobid = None
            else:
                if not job.finished:
                    return {"status": "uploading"}
                if not job.success:
                    transfer.jobid = None
                    raise RuntimeError(job.error or "Upload failed")

        # Also covers a backend restart or an expired rclone job record.
        response = requests.head(transfer.url.split("?", 1)[0], timeout=5)
        if response.ok and response.headers.get("Content-Type", "").split(";")[0] == "image/jpeg":
            transfer.ready = True
            return {"status": "ready", "urls": [transfer.url]}
        if response.status_code in (401, 403):
            raise ValueError("Public object is not accessible; check bucket visibility")
        if transfer.jobid is not None:
            raise RuntimeError("Uploaded object is not publicly available yet")
        with Session(engine) as db:
            media = db.get(Mediaitem, identifier)
            if not media or not media.processed.is_file():
                raise ValueError("Local finalized image is missing")
            path = media.processed
        transfer.attempts += 1
        job = self._rclone_client.copyfile_async(path.parent.absolute().as_posix(), path.name, transfer.remote.name, transfer.destination)
        transfer.jobid = job.jobid
        return {"status": "uploading"}

    @hookimpl
    def get_customer_result_status(self, identifier: UUID) -> dict | None:
        if not self._rclone_client or not self._customer_remote:
            return {"status": "failed", "error": self._storage_error}
        with self._customer_lock:
            transfer = self._customer_results.get(identifier)
            if not transfer:
                return None
            try:
                result = self._advance_customer(identifier, transfer)
            except Exception as exc:
                transfer.failures += 1
                raw = str(exc).lower()
                permanent = isinstance(exc, ValueError) or any(text in raw for text in ("403", "401", "signature", "accessdenied", "invalidaccess"))
                message = (
                    str(exc)
                    if isinstance(exc, ValueError)
                    else (
                        "Storage authentication failed; verify S3 credentials and region"
                        if permanent
                        else "Storage transfer or public verification failed; check connection and bucket configuration"
                    )
                )
                if permanent or transfer.failures >= 4:
                    transfer.error = message
                    result = {"status": "failed", "error": message}
                else:
                    # ponytail: one booth, one bounded retry schedule; use a durable queue only for multi-booth hosting.
                    transfer.retry_at = monotonic() + 2**transfer.failures
                    transfer.jobid = None
                    transfer.attempts = max(1, transfer.attempts)
                    result = {"status": "queued"}
            persisted = {**result, "attempts": transfer.attempts, "failures": transfer.failures}
            if self._delivery_state(identifier) != persisted:
                self._save_delivery(identifier, persisted)
            return result

    @hookimpl
    def kiosk_retry_customer_result(self, identifier: UUID) -> None:
        with self._customer_lock:
            transfer = self._customer_results.get(identifier)
            if transfer and (transfer.ready or not transfer.error):
                return
            self._customer_results.pop(identifier, None)
            self._save_delivery(identifier, {"status": "queued", "attempts": 0, "failures": 0})

    @hookimpl
    def collection_customer_result_deleted(self, identifier: UUID) -> None:
        if not self._rclone_client or not self._customer_remote:
            return
        with self._customer_lock:
            destination = Path(self._customer_remote.subdir, f"{identifier}.jpg").as_posix()
            self._rclone_client.deletefile(self._customer_remote.name, destination)
            self._customer_results.pop(identifier, None)

    @hookimpl
    def kiosk_storage_diagnostics(self) -> dict:
        return {"configured": bool(self._rclone_client and self._customer_remote), "message": self._storage_error}

    @hookimpl
    def kiosk_storage_health(self) -> bool:
        now = datetime.now(UTC)
        if self._storage_health and now - self._storage_health[0] < timedelta(minutes=5):
            return self._storage_health[1]
        healthy = False
        if self._rclone_client and self._customer_remote:
            from uuid import uuid4

            name = f".health-{uuid4()}.jpg"
            local = Path("tmp", name)
            remote_file = Path(self._customer_remote.subdir, name).as_posix()
            try:
                local.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (2, 2), "white").save(local, format="JPEG")
                self._rclone_client.copyfile(local.parent.absolute().as_posix(), local.name, self._customer_remote.name, remote_file)
                url = (
                    (self._customer_remote.shareconfig.manual_public_link or "")
                    .format(filename=name, identifier=name.removesuffix(".jpg"))
                    .split("?", 1)[0]
                )
                response = requests.head(url, timeout=5)
                healthy = response.ok and response.headers.get("Content-Type", "").split(";")[0] == "image/jpeg"
                self._storage_error = "" if healthy else f"Public storage check returned HTTP {response.status_code}"
            except Exception:
                self._storage_error = "Storage read/write check failed; verify runtime configuration, S3 credentials, region, and bucket"
                logger.warning(self._storage_error)
            finally:
                try:
                    self._rclone_client.deletefile(self._customer_remote.name, remote_file)
                except Exception:
                    healthy = False
                    self._storage_error = "Storage probe cleanup failed; verify delete access"
                local.unlink(missing_ok=True)
        self._storage_health = (now, healthy)
        return healthy
