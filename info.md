# Owlet Custom Integration

Unofficial, experimental fork of the archived
[ryanbdclark/owlet](https://github.com/ryanbdclark/owlet), maintained with the aid
of AI. Not affiliated with Owlet. Not a medical or safety system, and not a
replacement for the official hardware/app or alarms.

## Installation

1. Back up HA. Add `jensdufour/owlet` as a HACS custom **Integration** repository.
2. Download the fork and restart Home Assistant Core (2026.9.4 or newer).
3. Add **Owlet Smart Sock** in Devices & services; choose `europe` for EU accounts.

Do not install both forks together or delete an existing Owlet config entry just
to change the HACS source. See the [README](https://github.com/jensdufour/owlet)
for migration, freshness limits, validation scope and safe issue reporting.
