import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import resources
from pathlib import Path
from threading import Lock
from urllib.parse import quote
from uuid import UUID

import requests
from rclone_api.api import RcloneApi

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
        _immediate_sync_remotes = [x for x in self._config.remotes if x.enable_immediate_sync and x.enabled and x.sync_scope == "archive"]
        _full_sync_remotes = [x for x in self._config.remotes if x.enable_regular_sync and x.enabled and x.sync_scope == "archive"]
        _copy_sharepage_to_remotes = [x for x in self._config.remotes if x.enabled and x.enable_sharepage_sync and x.enabled]
        customer_remotes = [x for x in self._config.remotes if x.enabled and x.enable_immediate_sync and x.sync_scope == "customer_results"]
        self._customer_remote = customer_remotes[0] if customer_remotes else None
        if len(customer_remotes) > 1:
            logger.warning("only the first customer_results remote is used")

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

    @hookimpl
    def collection_customer_result_added(self, filepath_local: Path, identifier: UUID) -> None:
        if not self._rclone_client or not self._customer_remote:
            return
        if filepath_local.suffix.lower() not in (".jpg", ".jpeg"):
            return
        with self._customer_lock:
            existing = self._customer_results.get(identifier)
            if existing and not existing.error:
                return
            remote = self._customer_remote
            destination = Path(remote.subdir, f"{identifier}.jpg").as_posix()
            url = (remote.shareconfig.manual_public_link or "").format(filename=f"{identifier}.jpg", identifier=str(identifier))
            try:
                job = self._rclone_client.copyfile_async(
                    filepath_local.parent.absolute().as_posix(), filepath_local.name, remote.name, destination
                )
                self._customer_results[identifier] = CustomerResultTransfer(job.jobid, remote, destination, url)
            except Exception as exc:
                self._customer_results[identifier] = CustomerResultTransfer(None, remote, destination, url, str(exc))

    @hookimpl
    def get_customer_result_status(self, identifier: UUID) -> dict | None:
        if not self._rclone_client:
            return None
        with self._customer_lock:
            transfer = self._customer_results.get(identifier)
        if not transfer:
            return None
        if transfer.error:
            return {"status": "failed", "error": transfer.error}
        if not transfer.jobid:
            return {"status": "queued"}
        try:
            job = self._rclone_client.job_status(transfer.jobid)
            if not job.finished:
                return {"status": "uploading"}
            if not job.success:
                return {"status": "failed", "error": job.error or "upload failed"}
            if not transfer.url:
                return {"status": "failed", "error": "public customer-result URL is not configured"}
            response = requests.head(transfer.url.split("?", 1)[0], timeout=5)
            if not response.ok:
                return {"status": "failed", "error": f"public object check returned HTTP {response.status_code}"}
            return {"status": "ready", "urls": [transfer.url]}
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}

    @hookimpl
    def collection_customer_result_deleted(self, identifier: UUID) -> None:
        if not self._rclone_client or not self._customer_remote:
            return
        destination = Path(self._customer_remote.subdir, f"{identifier}.jpg").as_posix()
        try:
            self._rclone_client.deletefile(self._customer_remote.name, destination)
        finally:
            with self._customer_lock:
                self._customer_results.pop(identifier, None)

    @hookimpl
    def kiosk_storage_health(self) -> bool:
        now = datetime.now(UTC)
        if self._storage_health and now - self._storage_health[0] < timedelta(minutes=5):
            return self._storage_health[1]
        healthy = False
        if self._rclone_client and self._customer_remote:
            local = Path("tmp/kiosk-storage-health.txt")
            remote_file = Path(self._customer_remote.subdir, ".healthcheck").as_posix()
            try:
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_text("ok", encoding="ascii")
                self._rclone_client.copyfile(local.parent.absolute().as_posix(), local.name, self._customer_remote.name, remote_file)
                entries = self._rclone_client.ls(self._customer_remote.name, self._customer_remote.subdir)
                healthy = any(entry.Name == ".healthcheck" for entry in entries)
                self._rclone_client.deletefile(self._customer_remote.name, remote_file)
            except Exception as exc:
                logger.warning(f"customer storage health check failed: {exc}")
            finally:
                local.unlink(missing_ok=True)
        self._storage_health = (now, healthy)
        return healthy
