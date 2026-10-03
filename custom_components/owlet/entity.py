"""Base class for Owlet entities."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import OwletCoordinator


class OwletBaseEntity(CoordinatorEntity[OwletCoordinator], Entity):
    """Base class for Owlet Sock entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OwletCoordinator,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.sock = coordinator.sock

    @property
    def available(self) -> bool:
        """Reject missing fields and stale or charging-only vital readings."""
        description = self.entity_description
        properties = self.sock.properties
        return (
            super().available
            and properties.get(description.key) is not None
            and (
                description.available_during_charging
                or (
                    properties.get("charging") == 0
                    and (
                        description.key == "base_station_on"
                        or self.coordinator.vitals_fresh
                    )
                )
            )
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info of the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.sock.serial)},
            name=f"Owlet Sock {self.sock.serial}",
            connections={("mac", getattr(self.sock, "mac", "unknown"))},
            suggested_area="Nursery",
            configuration_url="https://my.owletcare.com/",
            manufacturer="Owlet Baby Care",
            model=getattr(self.sock, "model", None),
            sw_version=getattr(self.sock, "sw_version", None),
            hw_version=getattr(self.sock, "hw_version", "3r8"),
        )
