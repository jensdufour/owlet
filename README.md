# Owlet Custom Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]

[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

A custom component for the Owlet smart sock.

## Fork and AI disclaimer

This is an **unofficial, experimental maintenance fork** of
[ryanbdclark/owlet](https://github.com/ryanbdclark/owlet), whose repository is
archived. We are working on this fork **with the aid of AI**. AI-assisted changes
are reviewed and tested, but that does not guarantee correctness or reliability.
Original authors retain their attribution and the existing MIT license.

This project is not affiliated with or endorsed by Owlet. It depends on an
unofficial cloud API and can fail, lag, or stop working without notice. **Do not
use it for medical decisions, as a safety system, or as your sole alarm.** Keep
using the official Owlet hardware/app and the manufacturer's instructions.
Installing this integration does not validate medical accuracy or alarm delivery.

## Installation

Requires Home Assistant **2026.9.4 or newer**. The integration keeps the `owlet`
domain: do not install the upstream and this fork side by side.

1. Back up Home Assistant. In HACS, add `https://github.com/jensdufour/owlet`
	under **Custom repositories**, category **Integration**.
2. Download **Owlet** from this fork, then restart Home Assistant Core.
3. Open **Settings > Devices & services > Add integration > Owlet Smart Sock**.
	Select `europe` for an EU account, otherwise `world`, and enter your Owlet login.

When switching from upstream, preserve the existing Owlet config entry and device
registry. Replace only the HACS source/package. Existing account identities migrate
to include the region; device/entity unique IDs remain unchanged. If HACS refuses
two repositories for the same domain, remove the old HACS download first, install
the fork before restarting, and do not delete the configured integration.

The password is used for sign-in, not saved by this integration. HA stores the
account and refresh tokens in its own config-entry storage; protect HA backups.
Never post passwords, tokens, device serials, raw cloud responses or unredacted
diagnostics in an issue.


<!---->

## Usage

The `Owlet` integration offers integration with the Owlet Smart Sock cloud service. This provides sensors such as heart rate, oxygen saturation, charge percentage.

This integration provides the following entities:

- Binary sensors - charging status, high heart rate alert, low heart rate alert, high oxygen alert, low oxygen alert, low battery alert, lost power alert, sock diconnected alert, and sock status.
- Sensors - battery level, oxygen saturation, oxygen saturation 10 minute average, heart rate, battery time remaining, signal strength, and skin temperature.
- Where the device exposes them: sleep state, awake state, movement, and a
	diagnostic **Last cloud update** timestamp for V3 socks.

The existing base-station switch and its charging restriction are retained;
stale vitals do not prevent an explicit manual switch action. No alarm-silencing controls,
automatic device restarts, or baby-care automations are added.

## Options

- Seconds between polling - Number of seconds between each call for data from the owlet cloud service, default is 5 seconds.
- Minimum 5 seconds. Saving a changed interval reloads only the Owlet entry.
	Ordinary token refreshes do not reload it. Cloud operations time out after
	30 seconds; temporary connection/discovery failures use HA's native retry path.

## Freshness and limitations

V3 vital/sleep entities become unavailable while charging, when required fields
are missing, or when the cloud's `REAL_TIME_VITALS.data_updated_at` is absent,
invalid, in the future, or older than **120 seconds**. Last cloud update is the
source timestamp, not a claim that each successful poll obtained a new sample.
Diagnostic/alert values can still be old; check the source timestamp. V2 lacks a
shared vitals timestamp and does not get this freshness check.

This detects stale V3 vitals; it does **not** repair an upstream cloud/base-station
freeze. Old samples while charging or monitoring is off are normal. Sensor
support varies by model, firmware, region and app. Camera support, next sleep
windows, recovery-mode controls and the upstream transient charging/battery spike
remain outside this release. Long-running active monitoring, real token expiry,
world-region accounts and physical alarm delivery have not been live-validated.

## Development and verification

Version `2026.10.1` has eleven isolated regressions using actual HA `2026.9.4`
classes and Python `3.14.6`. They cover modern options/coordinator APIs, token and
reauthentication handling, region migration, retry behavior and sparse/stale data.
A bounded EU sign-in/device/property check passed for one charging V3 sock; this
is not an active-monitoring or medical validation. `pyowletapi==2025.4.1` is pinned
deliberately to the upstream's reverted version, not its incompatible release pin.

```sh
python -m pip install homeassistant==2026.9.4 pyowletapi==2025.4.1
python tests/check_runtime.py
```

Run in an isolated Linux environment with Python 3.14, not in your production HA
environment. The workflow also runs the native checks inside HA's release image.
The older `test_*.py` files are inherited HA Core fixtures, not a standalone test
suite; this fork's runnable regression entry point is `tests/check_runtime.py`.

For a release, validate the changes, commit and tag them, then attach `owlet.zip`
created with `git archive --format=zip <tag>:custom_components/owlet` to that
GitHub release. HACS installs the published archive. Report reproducible failures
in [this fork's issues](https://github.com/jensdufour/owlet/issues).

---

[commits-shield]: https://img.shields.io/github/commit-activity/w/jensdufour/owlet?style=for-the-badge
[commits]: https://github.com/jensdufour/owlet/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: LICENSE
[license-shield]: https://img.shields.io/github/license/jensdufour/owlet.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/status-experimental%20AI--assisted%20fork-orange.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jensdufour/owlet.svg?style=for-the-badge
[releases]: https://github.com/jensdufour/owlet/releases
[user_profile]: https://github.com/jensdufour
[add-integration]: https://my.home-assistant.io/redirect/config_flow_start?domain=owlet
[add-integration-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
