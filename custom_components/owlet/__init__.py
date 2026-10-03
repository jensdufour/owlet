"""The Owlet Smart Sock integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from aiohttp import ClientError
from pyowletapi.api import OwletAPI
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletDevicesError,
    OwletEmailError,
    OwletPasswordError,
)
from pyowletapi.sock import Sock

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_OWLET_EXPIRY, CONF_OWLET_REFRESH, DOMAIN, POLLING_INTERVAL, SUPPORTED_VERSIONS
from .coordinator import OwletCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Include the API region in existing account identities."""
    if entry.version > 2:
        return False
    if entry.version == 1:
        hass.config_entries.async_update_entry(
            entry,
            unique_id=f"{entry.data[CONF_REGION]}_{entry.data[CONF_USERNAME].lower()}",
            version=2,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Owlet Smart Sock from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    owlet_api = OwletAPI(
        region=entry.data[CONF_REGION],
        token=entry.data[CONF_API_TOKEN],
        expiry=entry.data[CONF_OWLET_EXPIRY],
        refresh=entry.data[CONF_OWLET_REFRESH],
        session=async_get_clientsession(hass),
    )

    try:
        async with asyncio.timeout(30):
            if token := await owlet_api.authenticate():
                hass.config_entries.async_update_entry(entry, data={**entry.data, **token})

            devices = await owlet_api.get_devices(SUPPORTED_VERSIONS)

    except (OwletAuthenticationError, OwletEmailError, OwletPasswordError) as err:
        _LOGGER.error("Credentials no longer valid, please setup owlet again")
        raise ConfigEntryAuthFailed(
            f"Credentials expired for {entry.data[CONF_USERNAME]}"
        ) from err

    except (OwletConnectionError, ClientError, TimeoutError) as err:
        raise ConfigEntryNotReady("Unable to connect to Owlet") from err

    except OwletDevicesError as err:
        raise ConfigEntryNotReady("No supported Owlet socks found") from err

    if "tokens" in devices:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, **devices["tokens"]}
        )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, POLLING_INTERVAL)
    coordinators = {
        device["device"]["dsn"]: OwletCoordinator(
            hass, Sock(owlet_api, device["device"]), scan_interval, entry
        )
        for device in devices["response"]
    }

    await asyncio.gather(
        *(
            coordinator.async_config_entry_first_refresh()
            for coordinator in list(coordinators.values())
        )
    )

    hass.data[DOMAIN][entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply polling options without restarting Home Assistant."""
    interval = timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, POLLING_INTERVAL))
    coordinators = hass.data[DOMAIN][entry.entry_id].values()
    if any(coordinator.update_interval != interval for coordinator in coordinators):
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
