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

`kiosk.payment_enabled` must remain `false` until the TB74 is electrically qualified, the admin password has changed from `0000`, and the camera, printer, minimum free disk, and private-cloud health checks all pass. No production validator driver is included yet.

Test mode is camera-only: it bypasses payment, printer, disk, cloud, and changed-password readiness, but never bypasses camera readiness.

## Supabase private storage

This repository contains only the private-bucket migration and disabled configuration examples. Runtime customer-result upload is intentionally inactive pending an approved Supabase endpoint and server credentials; do not enable paid operation on this scaffold alone.

1. Create a dedicated Supabase project and run `supabase db push` from this directory.
2. Deploy `cleanup-booth-media`, set `CLEANUP_SECRET`, replace the placeholders in `supabase/cron/cleanup-booth-media.sql.example`, and run it once in the Supabase SQL editor to schedule the authenticated hourly cleanup.
3. Create S3 access keys in Supabase Storage settings. Copy `config/rclone.supabase.example.conf` to `photobooth-data/config/rclone.conf` and replace placeholders.
4. Copy the synchronizer example into the plugin configuration and verify the remote with rclone.
5. Keep the bucket private and do not add anonymous object policies. S3 credentials are server secrets and bypass RLS.
6. Add and enable a customer-result uploader only after approving the concrete Supabase project endpoint and server credentials. Regular folder synchronization must stay disabled for this remote.

The intended object contract is `booths/{booth_id}/results/{media_id}.jpg` with seven-day signed URLs. Local retention already hard-deletes only media IDs recorded by completed kiosk sessions after seven days; cloud upload and expiry do not run until the uploader is implemented and enabled.

## TB74 qualification gate

Before writing or enabling a driver, record:

- Exact TB74/TB74B model and Philippine denomination firmware.
- Pulse or RS232 interface mode.
- Official harness pinout and inhibit polarity.
- Pulse width and pulse-count mapping for ₱50, ₱100, and ₱200.
- Opto-isolated controller and separate regulated 12 V supply.
- Fail-safe inhibition on controller, USB, application, or network failure.

Never connect the validator directly to PC USB or low-voltage GPIO. Machine-learning banknote recognition may be advisory only and must never grant credit.
