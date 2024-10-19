"""Sensor management."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .db import get_contracts, get_custom_sensors
from .sensors import constant_sensor, contract_sensor, custom_sensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up sensor platform from a config entry."""
    contracts = await hass.async_add_executor_job(get_contracts, config_entry.entry_id)
    custom_sensors = await hass.async_add_executor_job(
        get_custom_sensors, config_entry.entry_id
    )
    api = hass.data[DOMAIN][config_entry.entry_id]
    entity_registry = er.async_get(hass)

    sensors = []
    for contract in contracts:
        # Check if the sensor already exists in the entity registry
        if entity_registry.async_get_entity_id(
            DOMAIN, "sensor", contract[10].strip("sensor.")
        ):
            continue

        # If it doesn't exist, create the sensor and add to list
        sensor = contract_sensor.ContractSensor(hass, contract, api, config_entry)
        sensors.append(sensor)

    for contract in custom_sensors:
        sensor = custom_sensor.CustomSensor(hass, contract[3], contract[2])
        sensor_afname = custom_sensor.CustomSensor(
            hass, contract[3], contract[2], "afname"
        )
        sensor_injectie = custom_sensor.CustomSensor(
            hass, contract[3], contract[2], "injectie"
        )
        sensors.append(sensor)
        sensors.append(sensor_afname)
        sensors.append(sensor_injectie)

    sensors.append(constant_sensor.ConstSensor(hass, config_entry, api))

    async_add_entities(sensors, update_before_add=True)
