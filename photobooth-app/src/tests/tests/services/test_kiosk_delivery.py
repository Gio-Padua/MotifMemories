"""Run with python -m unittest discover -s src/tests/tests/services -p test_kiosk_delivery.py."""

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import requests
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from photobooth.appconfig import appconfig
from photobooth.database.models import Base, KioskPaymentSession, Mediaitem
from photobooth.plugins.synchronizer.config import RemoteConfig, ShareConfig
from photobooth.plugins.synchronizer.synchronizer import Synchronizer
from photobooth.services.collection import MediacollectionService
from photobooth.services.config.groups.actions import CollageProcessing
from photobooth.services.kiosk_filters import FILTERS, compose_look
from photobooth.services.kiosk_payment import KioskPaymentRequiredError, KioskPaymentService, KioskResultNotFoundError
from photobooth.services.mediaprocessing.processes import process_and_generate_collage


class KioskDeliveryTest(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.directory = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.engine = create_engine(f"sqlite:///{self.directory / 'test.sqlite'}", connect_args={"check_same_thread": False})
        self.stack.callback(self.engine.dispose)
        Base.metadata.create_all(self.engine)
        for module in (
            "services.kiosk_payment",
            "services.collection",
            "services.mediacollection.database",
            "services.mediacollection.cache",
            "plugins.synchronizer.synchronizer",
        ):
            self.stack.enter_context(patch(f"photobooth.{module}.engine", self.engine))
        self.collection = MediacollectionService()
        self.service = KioskPaymentService(MagicMock(), self.collection, MagicMock())
        self.service.emit = MagicMock()
        self.service._readiness = MagicMock(return_value={"ready": True})
        self.grant = self.service.create_test_grant()
        self.action = appconfig.kiosk.protected_action_names[0]
        self.service.reserve_capture(self.action, self.grant)
        self.media = self.make_media()
        self.service.complete_capture(self.media.id)

    def make_media(self):
        identifier = uuid4()
        source = self.directory / f"{identifier}.png"
        layer = Image.new("RGBA", (1200, 1800))
        ImageDraw.Draw(layer).rectangle((100, 100, 1100, 1500), fill=(180, 90, 55, 255))
        layer.save(source)
        overlay = self.directory / "overlay.png"
        artwork = Image.new("RGBA", (1200, 1800))
        ImageDraw.Draw(artwork).rectangle((0, 1650, 1199, 1799), fill="#F4B8C2")
        artwork.save(overlay)
        config = CollageProcessing(
            canvas_width=1200,
            canvas_height=1800,
            merge_definition=[],
            canvas_fill_background_enable=True,
            canvas_fill_background_color="#F7F3EB",
            canvas_img_front_enable=True,
            canvas_img_front_file=overlay,
        )
        processed = self.directory / f"{identifier}.jpg"
        compose_look(source, config, "original").save(processed)
        media = Mediaitem(
            id=identifier,
            job_identifier=uuid4(),
            media_type="collage",
            processed=processed,
            filter_source=source,
            pipeline_config=config.model_dump(mode="json"),
        )
        self.collection.add_item(media)
        return media

    def session(self):
        with Session(self.engine) as db:
            return db.get(KioskPaymentSession, 1)

    def ready_sync(self):
        sync = Synchronizer()
        sync._rclone_client = MagicMock()
        sync._rclone_client.copyfile_async.return_value = SimpleNamespace(jobid=7)
        sync._rclone_client.job_status.return_value = SimpleNamespace(finished=True, success=True)
        sync._customer_remote = RemoteConfig(
            enabled=True,
            sync_scope="customer_results",
            name="supabase:",
            subdir="photobooth-testloc/booths/booth-001/results",
            shareconfig=ShareConfig(
                enabled=True, use_sharepage=False, manual_public_link="https://example.test/{identifier}.jpg?download=Motif-Moments-{identifier}.jpg"
            ),
        )
        return sync

    def test_keep_finalize_print_and_direct_capture_guards(self):
        print_index = next(
            index
            for index, action in enumerate(appconfig.share.actions)
            if action.handles_images_only and action.trigger.ui_trigger.show_button and not action.processing.ask_user_for_parameter_input
        )
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.print_result(self.media.id, print_index, self.grant)
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.finalize_result(self.media.id, "mono", self.grant)
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.download_status(self.media.id)
        self.service.keep_result(self.media.id, self.grant)
        self.service.keep_result(self.media.id, self.grant)
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.reserve_capture(self.action, self.grant)
        result = self.service.finalize_result(self.media.id, "mono", self.grant)
        revision = result.revision
        self.assertEqual(self.session().presentation_stage, "delivery")
        self.assertEqual(self.service.finalize_result(self.media.id, "mono", self.grant).revision, revision)
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.finalize_result(self.media.id, "warm", self.grant)
        self.service.print_result(self.media.id, print_index, self.grant)
        self.service._share.share.assert_called_once()
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.print_result(self.media.id, print_index, self.grant)
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.reserve_capture(self.action, self.grant)

    def test_no_upload_before_finalization(self):
        self.assertIsNone(self.collection.get_item(self.media.id).customer_delivery)
        self.service.keep_result(self.media.id, self.grant)
        self.assertIsNone(self.collection.get_item(self.media.id).customer_delivery)
        self.service.finalize_result(self.media.id, "original", self.grant)
        self.assertEqual(self.collection.get_item(self.media.id).customer_delivery["status"], "queued")

    def test_filter_colors_and_source_are_preserved(self):
        source = self.media.filter_source.read_bytes()
        config = CollageProcessing(**self.media.pipeline_config)
        for look in FILTERS:
            output = compose_look(self.media.filter_source, config, look)
            self.assertEqual(output.size, (1200, 1800))
            self.assertEqual(output.getpixel((50, 50)), (247, 243, 235))
            self.assertEqual(output.getpixel((600, 1700)), (244, 184, 194))
            preview = compose_look(self.media.filter_source, config, look, preview=True)
            self.assertEqual(preview.size, (300, 450))
            if look == "mono":
                r, g, b = output.getpixel((600, 600))
                self.assertEqual((r, g), (g, b))
        self.assertEqual(self.media.filter_source.read_bytes(), source)

    def test_all_six_kiosk_layouts_render_every_look(self):
        actions = [action for action in appconfig.actions.collage if action.name in appconfig.kiosk.protected_action_names]
        self.assertEqual(len(actions), 6)
        for action in actions:
            capture_count = max(item.capture_index for item in action.processing.merge_definition if item.predefined_image is None) + 1
            captures = []
            for index in range(capture_count):
                path = self.directory / f"{action.name}-{index}.jpg"
                Image.new("RGB", (800, 600), (70 + index * 15, 120, 170)).save(path)
                captures.append(path)
            media = Mediaitem(
                id=uuid4(),
                job_identifier=uuid4(),
                media_type="collage",
                processed=self.directory / f"{action.name}.jpg",
                filter_source=self.directory / f"{action.name}.png",
                pipeline_config=action.processing.model_dump(mode="json"),
            )
            process_and_generate_collage(captures, media)
            with Image.open(media.filter_source) as source:
                self.assertEqual((source.mode, source.size), ("RGBA", (1200, 1800)))
            for look in FILTERS:
                with compose_look(media.filter_source, action.processing, look) as result:
                    self.assertEqual(result.size, (1200, 1800))

    def test_failed_render_rolls_back_and_original_can_be_used(self):
        self.service.keep_result(self.media.id, self.grant)
        original = self.media.processed.read_bytes()
        with patch("photobooth.services.kiosk_payment.render_look", side_effect=RuntimeError("fixture")):
            with self.assertRaises(RuntimeError):
                self.service.finalize_result(self.media.id, "warm", self.grant)
        self.assertEqual(self.media.processed.read_bytes(), original)
        self.assertEqual(self.session().presentation_stage, "filters")
        self.service.finalize_result(self.media.id, "original", self.grant)

    def test_keep_and_retake_cannot_both_win(self):
        def attempt(fn):
            try:
                fn()
                return True
            except KioskPaymentRequiredError:
                return False

        with ThreadPoolExecutor(2) as pool:
            results = list(
                pool.map(
                    attempt,
                    [lambda: self.service.keep_result(self.media.id, self.grant), lambda: self.service.reserve_capture(self.action, self.grant)],
                )
            )
        self.assertEqual(sum(results), 1)

    def test_invalid_grant_filter_and_unknown_id(self):
        with self.assertRaises(KioskPaymentRequiredError):
            self.service.keep_result(self.media.id, "bad")
        with self.assertRaises(ValueError):
            self.service.finalize_result(self.media.id, "unknown", self.grant)
        with self.assertRaises(KioskResultNotFoundError):
            self.service.download_status(uuid4())

    def test_upload_verification_restart_and_no_duplicate(self):
        self.service.keep_result(self.media.id, self.grant)
        self.service.finalize_result(self.media.id, "original", self.grant)
        sync = self.ready_sync()
        sync.collection_customer_result_added(self.media.processed, self.media.id)
        absent = SimpleNamespace(ok=False, status_code=404, headers={})
        present = SimpleNamespace(ok=True, status_code=200, headers={"Content-Type": "image/jpeg"})
        with patch("photobooth.plugins.synchronizer.synchronizer.requests.head", side_effect=[absent, present]):
            self.assertEqual(sync.get_customer_result_status(self.media.id)["status"], "uploading")
            self.assertEqual(sync.get_customer_result_status(self.media.id)["status"], "ready")
            self.assertEqual(sync.get_customer_result_status(self.media.id)["status"], "ready")
        self.assertEqual(sync._rclone_client.copyfile_async.call_count, 1)
        self.assertEqual(sync._rclone_client.copyfile_async.call_args.args[3], f"photobooth-testloc/booths/booth-001/results/{self.media.id}.jpg")
        restarted = self.ready_sync()
        restarted.collection_customer_result_added(self.media.processed, self.media.id)
        with patch("photobooth.plugins.synchronizer.synchronizer.requests.head", return_value=present):
            self.assertEqual(restarted.get_customer_result_status(self.media.id)["status"], "ready")
        restarted._rclone_client.copyfile_async.assert_not_called()

    def test_retry_is_bounded_and_errors_do_not_expose_secrets(self):
        sync = self.ready_sync()
        sync.collection_customer_result_added(self.media.processed, self.media.id)
        with patch("photobooth.plugins.synchronizer.synchronizer.requests.head", side_effect=requests.Timeout("secret fixture")):
            for _ in range(4):
                sync._customer_results[self.media.id].retry_at = 0
                result = sync.get_customer_result_status(self.media.id)
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("secret fixture", result["error"])
        sync.kiosk_retry_customer_result(self.media.id)
        self.assertEqual(sync._delivery_state(self.media.id)["status"], "queued")

    def test_storage_probe_uses_jpeg_and_cleans_up(self):
        sync = self.ready_sync()

        def inspect_upload(src, name, remote, destination):
            with Image.open(Path(src, name)) as image:
                self.assertEqual(image.format, "JPEG")
            self.assertTrue(destination.endswith(".jpg"))

        sync._rclone_client.copyfile.side_effect = inspect_upload
        with patch(
            "photobooth.plugins.synchronizer.synchronizer.requests.head",
            return_value=SimpleNamespace(ok=True, headers={"Content-Type": "image/jpeg"}),
        ):
            self.assertTrue(sync.kiosk_storage_health())
            self.assertTrue(sync.kiosk_storage_health())
        self.assertEqual(sync._rclone_client.copyfile.call_count, 1)
        sync._rclone_client.deletefile.assert_called_once()


if __name__ == "__main__":
    unittest.main()
