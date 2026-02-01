"""Support for Mapit Motorcycle sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, MapitDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MapitSensorEntityDescription(SensorEntityDescription):
    """Describes Mapit sensor entity."""

    value_fn: Callable[[dict], StateType] = lambda data: None


SENSORS: tuple[MapitSensorEntityDescription, ...] = (
    MapitSensorEntityDescription(
        key="speed",
        name="Speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        value_fn=lambda data: data.get("speed"),
    ),
    MapitSensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:motorbike",
        value_fn=lambda data: data.get("status"),
    ),
    MapitSensorEntityDescription(
        key="gps_accuracy",
        name="GPS Accuracy",
        native_unit_of_measurement="m",
        icon="mdi:crosshairs-gps",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("gps_accuracy"),
    ),
    MapitSensorEntityDescription(
        key="battery",
        name="Battery",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("battery"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Mapit sensors from config entry."""
    coordinator: MapitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities(
        MapitSensor(coordinator, config_entry, description)
        for description in SENSORS
    )


class MapitSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Mapit sensor."""

    entity_description: MapitSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MapitDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: MapitSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Motorcycle",
            "manufacturer": "Mapit",
            "model": "Vehicle Tracker",
        }

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.entity_description.value_fn(self.coordinator.data)
        return None
