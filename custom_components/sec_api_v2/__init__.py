"""Init file for sec-api-v2."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import SmartEnergyControlAPI
from .const import API_KEY, DOMAIN
from .services import format_id
from .db import (
    initialize_db,
    set_db_path,
    remove_all_except_entry_id,
    add_contract,
    add_custom_sensor,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Smart Energy Control component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Smart Energy Control from a config entry."""
    api_key = entry.data.get(API_KEY)

    api = SmartEnergyControlAPI(api_key)

    authenticated = await api.authenticate()
    if not authenticated:
        _LOGGER.error("Failed to authenticate with the Smart Energy Control API")
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api
    _LOGGER.info("Smart Energy Control setup complete")

    set_db_path(hass)
    initialize_db()

    remove_all_except_entry_id(entry.entry_id)  # Clean up database

    async def handle_generate_contracts_service(call):
        await async_handle_generate_contracts(hass, entry, call)

    hass.services.async_register(
        DOMAIN, "generate_contracts", handle_generate_contracts_service
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_track_state_removed_domain(hass: HomeAssistant, entry: ConfigEntry):
    """Listen for integration removal."""
    _LOGGER.info("Domain removed")


async def async_handle_generate_contracts(hass, entry, call):
    """Handle generate_contracts service."""
    contracts = call.data.get("contracts", [])
    _LOGGER.info(contracts)

    for contract in contracts:
        params = contract["id"].split("-_-")
        params = [x.replace("--", " ") for x in params]
        date_included = len(params) > 6

        if date_included:
            add_contract(
                entry.entry_id,
                params[4],
                params[2],
                params[5],
                params[0],
                params[1],
                params[3],
                params[6],
                params[7],
            )
        else:
            add_contract(
                entry.entry_id,
                params[4],
                params[2],
                params[5],
                params[0],
                params[1],
                params[3],
            )

        if date_included:
            contract_name = f"{params[0]} {params[1]} {params[4]} {params[2]} {params[3]} {params[5]} {params[6]} {params[7]}"

        else:
            contract_name = f"{params[0]} {params[1]} {params[4]} {params[2]} {params[3]} {params[5]}"
        contract_id = f"sensor.sec_{format_id(contract_name)}"

        add_custom_sensor(entry.entry_id, contract_id, contract["alias"])
        await hass.config_entries.async_reload(entry.entry_id)