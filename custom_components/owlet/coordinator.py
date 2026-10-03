"""Owlet integration coordinator class."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging

from aiohttp import ClientError
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletError,
)
from pyowletapi.sock import Sock

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class OwletCoordinator(DataUpdateCoordinator):
    """Coordinator is responsible for querying the device at a specified route."""

    def __init__(
        self, hass: HomeAssistant, sock: Sock, interval, entry: ConfigEntry
    ) -> None:
        """Initialise a custom coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.sock = sock

    @property
    def vitals_updated_at(self) -> datetime | None:
        """Return the V3 cloud sample timestamp, never the local poll time."""
        value = self.sock.raw_properties.get("REAL_TIME_VITALS", {}).get("data_updated_at")
        if not isinstance(value, str):
            return None
        try:
            timestamp = datetime.fromisoformat(value)
        except ValueError:
            return None
        return timestamp if timestamp.tzinfo is not None else None

    @property
    def vitals_fresh(self) -> bool:
        """Reject stale V3 samples; V2 has no shared vitals timestamp."""
        if self.sock.version != 3:
            return True
        timestamp = self.vitals_updated_at
        if timestamp is None:
            return False
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return 0 <= age <= 120

    async def _async_update_data(self) -> None:
        """Fetch the data from the device."""
        try:
            async with asyncio.timeout(30):
                properties = await self.sock.update_properties()
            if "tokens" in properties:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **properties["tokens"]},
                )
        except OwletAuthenticationError as err:
            raise ConfigEntryAuthFailed(
                "Owlet authentication expired; reauthenticate the account"
            ) from err
        except (OwletError, OwletConnectionError, ClientError, TimeoutError) as err:
            raise UpdateFailed("Unable to update Owlet readings") from err
