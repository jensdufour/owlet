# Owlet Maintenance Notes

- This is the experimental `jensdufour/owlet` fork of archived
  `ryanbdclark/owlet`. Preserve the MIT license and original attribution. Keep
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
- tests/check_runtime.py runs eleven isolated checks with native HA classes.
  The legacy tests were copied from a HA Core test environment and do not run
  standalone. Do not report them as passing without porting and running them.
- Initial live validation: EU login and one charging V3 sock's properties.
  No monitoring/alarm control was changed. Active/overnight readings and actual
  token-expiry recovery remain unverified; synthetic tests are not live proof.
- Release archive contains only custom_components/owlet contents at ZIP root,
  named owlet.zip. Install via the fork's HACS release, not a local production copy.