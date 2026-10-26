# Owlet Maintenance Notes

- Version2026.10.2 is a packaging-only update: bundled branding and corrected
  license documentation, without runtime, dependency or account changes.
- Bundle the original 256x256 Owlet PNG at custom_components/owlet/brand/icon.png.
  Home Assistant brands removed its central copy in c2bcb2f06d16a0c82f7963c47c33ce67b8634bf2;
  HACS therefore needs the integration-local asset. Source brands commit
  03dcc9c3436e48c295fe9ca3055ee5ddfda47cb3; icon Git blob
  06da0a79b6a8670cff9d13139c2176cc775fa0c5. Preserve the asset in release ZIPs.
- This is the experimental `jensdufour/owlet` fork of archived
  `ryanbdclark/owlet`. Preserve the Apache-2.0 license and original attribution. Keep
  the AI-assisted development and non-medical/safety disclaimers prominent.
- Preserve domain `owlet` and serial-based entity/device IDs. Account identity
  version 2 adds `europe_` or `world_`; migration must preserve data and options.
- HA 2026.9.4 owns OptionsFlow.config_entry and expects the coordinator entry
  explicitly. Never restore the old property setter or CONF_EMAIL lookup.
- Tokens can change during device discovery. Persist the final API tokens.
  Config-entry update listeners see token changes too: reload only for an actual
  interval change. Do not log credentials, tokens, responses or account data.
- Pin pyowletapi 2025.4.1 until a replacement passes import, EU authentication and
  property decoding. The upstream's 2025.4.3 release used an incompatible pin.
- Freshness uses the V3 cloud data_updated_at, not successful local polling or
  unchanged physiological values. The 120-second guard is not a medical SLA;
  charging may legitimately retain old samples. V2 has no shared timestamp.
- Version2026.10.1 exempts the existing manual base-station switch from sample
  freshness, retaining its original charging restriction. Do not prevent a user
  from manually starting monitoring just because stopped monitoring has old data.
- tests/check_runtime.py runs eleven isolated checks with native HA classes.
  The legacy tests were copied from a HA Core test environment and do not run
  standalone. Do not report them as passing without porting and running them.
- Initial live validation: EU login and one charging V3 sock's properties.
  No monitoring/alarm control was changed. Active/overnight readings and actual
  token-expiry recovery remain unverified; synthetic tests are not live proof.
- Release archive contains only custom_components/owlet contents at ZIP root,
  named owlet.zip. Install via the fork's HACS release, not a local production copy.