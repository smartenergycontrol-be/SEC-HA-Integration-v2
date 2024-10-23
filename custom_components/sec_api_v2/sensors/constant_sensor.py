"""Contract sensor definition."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConstSensor(SensorEntity):
    def __init__(self, hass, entry: ConfigEntry, api) -> None:
        self._name = "SEC: Constant values"
        self._state = 0
        self._hass = hass
        self._unique_id = "sensor.sec_constant_sensor"
        self._entry = entry
        self._api = api
        self._attributes = {}

        self.entity_id = self._unique_id

    @property
    def unique_id(self):
        """Return unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return name."""
        return self._name

    @property
    def state(self):
        """Return state."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return self._attributes

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await self._update_constants()
        self.async_write_ha_state()

    async def _update_constants(self):
        """Fetch constants from the API and update attributes."""
        zip_code = self._entry.data.get("zip_code")
        self._attributes = await self._api.get_constants(zip_code)
        self._state = self._attributes.get("postcode", 0)
        self.async_write_ha_state()
