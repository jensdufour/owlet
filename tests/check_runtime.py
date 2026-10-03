"""Run isolated regressions with HA installed: python tests/check_runtime.py."""

from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys
from tempfile import TemporaryDirectory
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiohttp import ClientConnectionError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from pyowletapi.exceptions import OwletAuthenticationError, OwletDevicesError

from custom_components.owlet import async_migrate_entry, async_setup_entry, async_update_options
from custom_components.owlet.config_flow import OwletConfigFlow
from custom_components.owlet.coordinator import OwletCoordinator
from custom_components.owlet.sensor import OwletSensor, OwletSleepSensor, SENSORS
from custom_components.owlet.binary_sensor import OwletAwakeSensor
from custom_components.owlet.switch import OwletBaseSwitch, SWITCHES


class RuntimeChecks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.hass = HomeAssistant(self.directory.name)
        self.hass.config_entries = Mock()
        self.entry = ConfigEntry(
            domain="owlet",
            title="Test account",
            data={"username": "test@example.invalid", "region": "europe"},
            options={},
            version=1,
            minor_version=1,
            unique_id="test@example.invalid",
            source="user",
            discovery_keys=MappingProxyType({}),
            subentries_data=[],
        )
        self.hass.config_entries.async_get_known_entry.return_value = self.entry

    async def test_options_use_managed_entry_and_default(self):
        flow = OwletConfigFlow.async_get_options_flow(self.entry)
        flow.hass = self.hass
        flow.handler = self.entry.entry_id
        result = await flow.async_step_init()
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["data_schema"]({}), {"scan_interval": 5})
        saved = await flow.async_step_init({"scan_interval": 10})
        self.assertEqual(saved["data"], {"scan_interval": 10})

    async def test_expired_token_requests_reauthentication(self):
        sock = SimpleNamespace(
            update_properties=AsyncMock(side_effect=OwletAuthenticationError())
        )
        coordinator = OwletCoordinator(self.hass, sock, 5, self.entry)
        with self.assertRaises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_transport_failure_marks_update_failed(self):
        for error in (ClientConnectionError(), TimeoutError()):
            with self.subTest(error=type(error).__name__):
                sock = SimpleNamespace(update_properties=AsyncMock(side_effect=error))
                coordinator = OwletCoordinator(self.hass, sock, 5, self.entry)
                with self.assertRaises(UpdateFailed):
                    await coordinator._async_update_data()

    async def test_options_reload_only_the_entry(self):
        self.hass.config_entries.async_reload = AsyncMock()
        coordinator = SimpleNamespace(update_interval=timedelta(seconds=10))
        self.hass.data["owlet"] = {self.entry.entry_id: {"test": coordinator}}
        await async_update_options(self.hass, self.entry)
        self.hass.config_entries.async_reload.assert_awaited_once_with(self.entry.entry_id)
        self.hass.config_entries.async_reload.reset_mock()
        coordinator.update_interval = timedelta(seconds=5)
        await async_update_options(self.hass, self.entry)
        self.hass.config_entries.async_reload.assert_not_called()

    async def test_missing_devices_retries_setup(self):
        entry = Mock(data={"region": "europe", "api_token": "test", "expiry": 1,
                           "refresh": "test", "username": "test@example.invalid"})
        api = SimpleNamespace(authenticate=AsyncMock(return_value=None),
                              get_devices=AsyncMock(side_effect=OwletDevicesError()))
        with patch("custom_components.owlet.OwletAPI", return_value=api), patch(
            "custom_components.owlet.async_get_clientsession"
        ), self.assertRaises(ConfigEntryNotReady):
            await async_setup_entry(self.hass, entry)

    async def test_login_stores_latest_tokens_and_region_identity(self):
        tokens = {"api_token": "fresh", "refresh": "new", "expiry": 100}
        api = SimpleNamespace(authenticate=AsyncMock(return_value={"api_token": "old"}),
                              get_devices=AsyncMock(), tokens=tokens)
        for region in ("europe", "world"):
            with self.subTest(region=region):
                flow = OwletConfigFlow()
                flow.hass = self.hass
                flow.async_set_unique_id = AsyncMock()
                flow._abort_if_unique_id_configured = Mock()
                with patch("custom_components.owlet.config_flow.OwletAPI", return_value=api), patch(
                    "custom_components.owlet.config_flow.async_get_clientsession"
                ):
                    result = await flow.async_step_user({"region": region,
                        "username": "Test@example.invalid", "password": "test"})
                flow.async_set_unique_id.assert_awaited_once_with(f"{region}_test@example.invalid")
                self.assertEqual(result["data"]["api_token"], "fresh")
                self.assertNotIn("password", result["data"])
        self.assertEqual(api.get_devices.await_count, 2)

    async def test_login_failure_is_actionable(self):
        for error, expected in ((OwletDevicesError(), "no_devices"),
                                (ClientConnectionError(), "cannot_connect")):
            with self.subTest(error=type(error).__name__):
                api = SimpleNamespace(authenticate=AsyncMock(return_value=None),
                                      get_devices=AsyncMock(side_effect=error))
                flow = OwletConfigFlow()
                flow.hass = self.hass
                flow.async_set_unique_id = AsyncMock()
                flow._abort_if_unique_id_configured = Mock()
                with patch("custom_components.owlet.config_flow.OwletAPI", return_value=api), patch(
                    "custom_components.owlet.config_flow.async_get_clientsession"
                ):
                    result = await flow.async_step_user({"region": "europe",
                        "username": "test@example.invalid", "password": "test"})
                self.assertEqual(result["errors"], {"base": expected})

    async def test_region_migration_preserves_account_data(self):
        before = dict(self.entry.data)
        self.assertTrue(await async_migrate_entry(self.hass, self.entry))
        self.hass.config_entries.async_update_entry.assert_called_once_with(
            self.entry, unique_id="europe_test@example.invalid", version=2
        )
        self.assertEqual(dict(self.entry.data), before)

    async def test_reauthentication_validates_before_updating(self):
        tokens = {"api_token": "fresh", "refresh": "new", "expiry": 100}
        api = SimpleNamespace(authenticate=AsyncMock(return_value=None),
                              get_devices=AsyncMock(), tokens=tokens)
        flow = OwletConfigFlow()
        flow.hass = self.hass
        flow.reauth_entry = self.entry
        self.hass.config_entries.async_reload = AsyncMock()
        with patch("custom_components.owlet.config_flow.OwletAPI", return_value=api), patch(
            "custom_components.owlet.config_flow.async_get_clientsession"
        ):
            result = await flow.async_step_reauth_confirm({"password": "test"})
        self.assertEqual(result["reason"], "reauth_successful")
        self.hass.config_entries.async_update_entry.assert_called_once_with(
            self.entry, data={**self.entry.data, **tokens})
        self.hass.config_entries.async_reload.assert_awaited_once_with(self.entry.entry_id)

    async def test_stale_vitals_and_missing_fields_are_unavailable(self):
        sock = SimpleNamespace(serial="test", version=3,
            properties={"charging": 0, "heart_rate": 100, "battery_percentage": 50},
            raw_properties={"REAL_TIME_VITALS": {"data_updated_at":
                (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()}})
        coordinator = OwletCoordinator(self.hass, sock, 5, self.entry)
        heart = OwletSensor(coordinator, next(item for item in SENSORS if item.key == "heart_rate"))
        battery = OwletSensor(coordinator, next(item for item in SENSORS if item.key == "battery_percentage"))
        self.assertTrue(heart.available)
        sock.raw_properties["REAL_TIME_VITALS"]["data_updated_at"] = (
            datetime.now(timezone.utc) - timedelta(seconds=121)).isoformat()
        self.assertFalse(heart.available)
        self.assertTrue(battery.available)
        sock.properties["base_station_on"] = False
        base_switch = OwletBaseSwitch(coordinator, SWITCHES[0])
        self.assertTrue(base_switch.available)
        sock.properties["charging"] = 1
        self.assertFalse(base_switch.available)
        sock.properties["charging"] = 0
        for timestamp in (None, "invalid", "2026-10-03T01:00:00"):
            sock.raw_properties["REAL_TIME_VITALS"]["data_updated_at"] = timestamp
            self.assertFalse(heart.available)
        sock.properties.pop("heart_rate")
        self.assertFalse(heart.available)
        self.assertIsNone(heart.native_value)

    async def test_charging_and_unknown_sleep_never_report_awake(self):
        sock = SimpleNamespace(serial="test", version=2,
            properties={"charging": 1, "sleep_state": 0}, raw_properties={})
        coordinator = OwletCoordinator(self.hass, sock, 5, self.entry)
        sleep = OwletSleepSensor(coordinator)
        awake = OwletAwakeSensor(coordinator)
        self.assertFalse(sleep.available)
        self.assertIsNone(awake.is_on)
        sock.properties.update(charging=0, sleep_state=99)
        self.assertIsNone(sleep.native_value)
        self.assertIsNone(awake.is_on)
        sock.properties["sleep_state"] = 1
        self.assertTrue(awake.is_on)


if __name__ == "__main__":
    unittest.main(verbosity=2)