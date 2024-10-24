"""Contract sensor definition."""

from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from ..db import update_sensor_id
from ..services import format_id

_LOGGER = logging.getLogger(__name__)


class ContractSensor(CoordinatorEntity, SensorEntity):
    """Representation of a contract sensor."""

    def __init__(
        self, hass: HomeAssistant, contract, api, config_entry: ConfigEntry
    ) -> None:
        """Initialize the contract sensor."""
        self._hass = hass
        self._api = api
        self._entry = config_entry
        (
            self._id,
            self._entry_id,
            self._energy_type,
            self._contract_type,
            self._segment,
            self._supplier,
            self._contract_name,
            self._price_component,
            self._month,
            self._year,
            self._sensor_id,
        ) = contract

        self._name = f"SEC: {self._supplier}, {self._contract_name}, {self._price_component}, {self._energy_type}, {self._contract_type}"

        if self._month in [None, "NULL"] and self._year in [None, "NULL"]:
            _id = f"sec_{self._supplier}_{self._contract_name}_{self._energy_type}_{self._contract_type}_{self._price_component}_{self._segment}"
        else:
            _id = f"sec_{self._supplier}_{self._contract_name}_{self._energy_type}_{self._contract_type}_{self._price_component}_{self._segment}_{self._month}_{self._year}"
        formatted_id = format_id(_id)
        self._unique_id = formatted_id
        self.entity_id = async_generate_entity_id("sensor.{}", formatted_id, hass=hass)

        update_sensor_id(
            self.entity_id,
            self._energy_type,
            self._contract_type,
            self._segment,
            self._supplier,
            self._contract_name,
            self._price_component,
            self._month,
            self._year,
        )

        self.coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="Contract Data",
            update_method=self._fetch_data,
            update_interval=self._get_update_interval(),
        )

        hass.async_create_task(self.coordinator.async_config_entry_first_refresh())

        super().__init__(self.coordinator)

    def _get_update_interval(self):
        """Determine update interval to refresh on the hour and every 10 minutes between 12pm and 2pm."""
        now = datetime.now()

        if now.hour >= 12 and now.hour < 14:
            return timedelta(minutes=10)

        next_full_hour = (now + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        return next_full_hour - now

    async def _fetch_data(self):
        """Fetch data from API or other source with contract-specific attributes."""
        try:
            api_data = await self._api.get_prijsonderdelen(
                maand=self._month,
                jaar=self._year,
                energietype=self._energy_type,
                vast_variabel_dynamisch=self._contract_type,
                segment=self._segment,
                handelsnaam=self._supplier,
                productnaam=self._contract_name,
                prijsonderdeel=self._price_component,
                postcode=self._entry.data.get("zip_code", "2000"),
                show_prices="yes",
            )
            if api_data and api_data[0]:
                self._state = f"{api_data[0].get('handelsnaam')}: {api_data[0].get('productnaam')}"
                self._attributes = api_data[0]
                return {
                    self._id: {"state": self._state, "attributes": self._attributes}
                }

        except Exception:
            _LOGGER.error("Error fetching data")

        return {self._id: {"state": self._state, "attributes": self._attributes}}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self.coordinator.data
        if data and self._id in data:
            attrs = data[self._id]["attributes"]
            return f"{attrs.get("handelsnaam")}: {attrs.get("productnaam")}"
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = self.coordinator.data
        if data and self._id in data:
            data[self._id]["attributes"].update({"icon": "mdi:currency-eur"})
            return data[self._id]["attributes"]
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # _LOGGER.info(f"Updating coordinator for {self._name}")
        self.async_write_ha_state()
