# Paid kiosk commissioning

Paid operation is locked by default. Use the hidden five-tap top-right gesture and choose **Start test session** while commissioning.

## Operator access

- Username: `admin`
- Initial password: `0000`
- `0000` is setup-only. Change it to at least 12 characters in Admin → Configuration before payments can be enabled.
- Five failed logins lock that browser address for five minutes.
- A test grant stays only in the current Pinia memory and expires after four hours or on reload.
- **Void active session** is operator recovery; it forfeits the active session.

## Payment policy

- Session price: ₱200 by default; configure `kiosk.price_php` for a different amount.
- Accepted notes: ₱50, ₱100, ₱200
- Exact amount is recommended. Overpayment is recorded and no change is returned.
- Partial credit is forfeited 90 seconds after the first accepted note.
- One complete retake and one print are included. Keep these photos closes retake permanently; the next step selects Original, Soft, Warm, or Mono. Only the kept, finalized collage can be printed or uploaded.

`kiosk.payment_enabled` must remain `false` until the TB74 is electrically qualified, the admin password has changed from `0000`, and the camera, printer, minimum free disk, and customer-storage health checks all pass. No production validator driver is included yet.

Test mode is camera-only: it bypasses payment, printer, disk, cloud, and changed-password readiness, but never bypasses camera readiness.

## Supabase public QR storage

The kiosk uploads kept, filter-finalized paid/test collage JPEGs directly with rclone. Guests scan a QR code for the public object URL; no customer website or Supabase client is used. Test mode bypasses readiness gates but still performs real uploads when storage is configured.

1. Create a dedicated Supabase project and run `supabase db push` from this directory.
2. Deploy `cleanup-booth-media`, set `CLEANUP_SECRET`, replace the placeholders in `supabase/cron/cleanup-booth-media.sql.example`, and run it once in the Supabase SQL editor to schedule the authenticated hourly cleanup.
3. Create S3 access keys in Supabase Storage settings. Copy `config/rclone.supabase.example.conf` to `photobooth-data/config/rclone.conf` and replace placeholders.
4. Copy `config/plugin_synchronizer.supabase.example.json` to `photobooth-data/config/plugin_synchronizer.json`, replace no URL values, and enable the plugin after the rclone remote passes a manual copy test.
5. Keep `photobooth-testloc` public. Keep S3 credentials only in ignored `photobooth-data/config/rclone.conf`; they are server secrets and bypass RLS.
6. Keep regular and share-page synchronization disabled for the `customer_results` remote. Immediate upload is the only enabled mode.

The object contract is `photobooth-testloc/booths/booth-001/results/{media_id}.jpg`. The API returns a direct URL ending in `?download=Motif-Moments-{media_id}.jpg`. Public URLs do not expire; booth cleanup and the independent hourly Supabase function delete objects after seven days.

Each kiosk photo uses a 10-second display countdown followed by the full 2.4-second smile WebP and a 0.3-second static hold. Restart Photobooth after installing presets so all six actions receive the cue settings.

### Runtime configuration and troubleshooting

Start the backend from `E:\photobooth\photobooth-data`, for example in Git Bash:

```bash
cd /e/photobooth/photobooth-data
../ptbth/Scripts/photobooth.exe
```

The backend reads `config/rclone.conf` and `config/plugin_synchronizer.json` relative to that working directory. Editing `E:\photobooth\config\rclone.supabase.example.conf` alone has no effect. Keep example files as placeholders; credentials belong only in the ignored runtime configuration. No frontend `.env` is required.

The September 2026 diagnosis found both runtime files missing and `Synchronizer Plugin is disabled` in the backend log. The S3 credentials in the example successfully listed the target bucket. These are separate checks: successful S3 authentication does not enable the plugin or prove public download access.

After configuration changes, restart the backend. Operator setup displays sanitized storage diagnostics. The storage health probe uses a tiny JPEG because this bucket only allows `image/jpeg`; it verifies upload, public HEAD access, and deletion, cached for five minutes.

Result delivery is durable in SQLite. Transient failures retry three times with 2/4/8-second backoff. Authentication/configuration errors wait for correction. The QR dialog offers Retry, polls every two seconds for up to 60 seconds, and cancels when closed. Restart recovery checks the exact public object before uploading a missing finalized JPEG again. Do not enable full-folder or share-page sync on this remote.

### Review and filters

Review requires an explicit Keep decision. Its existing 30-second idle timeout closes the session without uploading an unconfirmed result. Keep closes retake on the server. The four-look picker automatically confirms its selection after 30 idle seconds; a reload before confirmation resets the uncommitted selection to Original. The final JPEG is rendered once from a pristine RGBA photo layer, with frame, background, and text added afterward.

Printing waits for local finalization; QR waits for public upload verification. A processing error preserves the source and offers Retry or Use Original. Rendering, printing, and QR loading pause the delivery timeout. Backend restarts recover a committed rendering choice. Existing pre-migration results keep their prior delivery behavior.

The SQLite migration runs automatically at backend startup. Back up `database/database.sqlite` with the backend stopped before deploying. The source layer, filter previews, and captures associated with an expired kiosk job are included in local retention; only the final JPEG belongs in cloud storage.

## TB74 qualification gate

Before writing or enabling a driver, record:

- Exact TB74/TB74B model and Philippine denomination firmware.
- Pulse or RS232 interface mode.
- Official harness pinout and inhibit polarity.
- Pulse width and pulse-count mapping for ₱50, ₱100, and ₱200.
- Opto-isolated controller and separate regulated 12 V supply.
- Fail-safe inhibition on controller, USB, application, or network failure.

Never connect the validator directly to PC USB or low-voltage GPIO. Machine-learning banknote recognition may be advisory only and must never grant credit.
