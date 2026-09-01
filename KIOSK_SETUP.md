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
- One complete retake and one print are included. Printing closes retake; retaking makes only the new collage printable.

`kiosk.payment_enabled` must remain `false` until the TB74 is electrically qualified, the admin password has changed from `0000`, and the camera, printer, minimum free disk, and customer-storage health checks all pass. No production validator driver is included yet.

Test mode is camera-only: it bypasses payment, printer, disk, cloud, and changed-password readiness, but never bypasses camera readiness.

## Supabase public QR storage

The kiosk uploads final paid/test collage JPEGs directly with rclone. Guests scan a QR code for the public object URL; no customer website or Supabase client is used.

1. Create a dedicated Supabase project and run `supabase db push` from this directory.
2. Deploy `cleanup-booth-media`, set `CLEANUP_SECRET`, replace the placeholders in `supabase/cron/cleanup-booth-media.sql.example`, and run it once in the Supabase SQL editor to schedule the authenticated hourly cleanup.
3. Create S3 access keys in Supabase Storage settings. Copy `config/rclone.supabase.example.conf` to `photobooth-data/config/rclone.conf` and replace placeholders.
4. Copy `config/plugin_synchronizer.supabase.example.json` to `photobooth-data/config/plugin_synchronizer.json`, replace no URL values, and enable the plugin after the rclone remote passes a manual copy test.
5. Keep `photobooth-testloc` public. Keep S3 credentials only in ignored `photobooth-data/config/rclone.conf`; they are server secrets and bypass RLS.
6. Keep regular and share-page synchronization disabled for the `customer_results` remote. Immediate upload is the only enabled mode.

The object contract is `photobooth-testloc/booths/booth-001/results/{media_id}.jpg`. The API returns a direct URL ending in `?download=Motif-Moments-{media_id}.jpg`. Public URLs do not expire; booth cleanup and the independent hourly Supabase function delete objects after seven days.

Each kiosk photo uses a 10-second display countdown followed by the full 2.4-second smile WebP and a 0.3-second static hold. Restart Photobooth after installing presets so all six actions receive the cue settings.

## TB74 qualification gate

Before writing or enabling a driver, record:

- Exact TB74/TB74B model and Philippine denomination firmware.
- Pulse or RS232 interface mode.
- Official harness pinout and inhibit polarity.
- Pulse width and pulse-count mapping for ₱50, ₱100, and ₱200.
- Opto-isolated controller and separate regulated 12 V supply.
- Fail-safe inhibition on controller, USB, application, or network failure.

Never connect the validator directly to PC USB or low-voltage GPIO. Machine-learning banknote recognition may be advisory only and must never grant credit.
