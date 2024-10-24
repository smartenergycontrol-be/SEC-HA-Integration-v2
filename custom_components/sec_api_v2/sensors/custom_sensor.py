from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event

from ..services import format_id


class CustomSensor(SensorEntity):
    """Representation of a custom sensor that tracks an existing sensor."""

    def __init__(self, hass, custom_sensor_name, original_sensor_id, sensor_type="all"):
        self.hass = hass
        self._custom_sensor_name = custom_sensor_name
        self._original_sensor_id = original_sensor_id
        self._state = None
        self._attributes = None
        self._unsub = None
        self._sensor_type = sensor_type
        self._unique_id = f"sensor.{format_id(self._custom_sensor_name)}"

        if sensor_type == "afname":
            self._custom_sensor_name += " Afname"
            self._unique_id += "_afname"
        if sensor_type == "injectie":
            self._custom_sensor_name += " Injectie"
            self._unique_id += "_injectie"

        self.entity_id = self._unique_id

    @property
    def name(self):
        """Return the custom sensor name."""
        return self._custom_sensor_name

    @property
    def unique_id(self):
        """Return the unique entity id."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the custom sensor, which tracks the original sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return attributes."""
        return self._attributes

    async def async_added_to_hass(self):
        """Register callbacks when sensor is added to hass."""

        @callback
        def state_listener(event):
            """Handle state changes of the original sensor."""
            new_state = event.data.get("new_state")
            if new_state:
                try:
                    self._state = float(new_state.state)
                except (ValueError, TypeError):
                    self._state = 0
                self._attributes = new_state.attributes
                self.async_write_ha_state()

        # Subscribe to state changes for the original sensor
        self._unsub = async_track_state_change_event(
            self.hass, self._original_sensor_id, state_listener
        )

        # Initial update to get the current state of the sensor
        await self.async_update()

    async def async_will_remove_from_hass(self):
        """Remove state listener when entity is removed."""
        if self._unsub is not None:
            self._unsub()

    async def async_update(self):
        """Update the sensor by fetching the state and attributes of the original sensor."""
        original_sensor = self.hass.states.get(self._original_sensor_id)
        if original_sensor:
            if self._sensor_type == "afname":
                self._state = original_sensor.attributes.get("prices_afname", {}).get(
                    "current_price", 0
                )
                self._attributes = {
                    "state_class": "measurement",
                    "unit_of_measurement": "EUR/kWh",
                }
            if self._sensor_type == "injectie":
                self._state = original_sensor.attributes.get("prices_injectie", {}).get(
                    "current_price", 0
                )
                self._attributes = {
                    "state_class": "measurement",
                    "unit_of_measurement": "EUR/kWh",
                }
            if self._sensor_type == "all":
                self._state = original_sensor.state
                self._attributes = original_sensor.attributes
