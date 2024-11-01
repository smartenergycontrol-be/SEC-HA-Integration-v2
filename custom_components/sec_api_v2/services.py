"""Helper functions."""

import logging

from homeassistant.core import HomeAssistant

import re
from .db import add_contract, add_custom_sensor, add_top_contract
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def format_id(input_str):
    """Format ids to hass standards."""
    input_str = input_str.replace("@", "a").replace("+", "_plus")
    formatted_str = re.sub(r"\W+", "_", input_str)
    formatted_str = re.sub(r"_+", "_", formatted_str)
    return formatted_str.strip("_").lower()


async def async_handle_generate_contracts(hass, entry, call):
    """Handle generate_contracts service."""
    contracts = call.data.get("contracts", [])

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


async def async_handle_fetch_best_contracts(hass: HomeAssistant, entry):
    _LOGGER.info("Settup up best contracts")
    api = hass.data.setdefault(DOMAIN, {})[entry.entry_id]
    energy_type = entry.data.get("conf_top_energy_type", "")
    segment = entry.data.get("conf_top_segment", "")
    contract_type = entry.data.get("conf_top_contract_type", "")
    amount = entry.data.get("conf_top_contracts_limit", "5")

    data = await api.get_prijsonderdelen(
        energietype=energy_type,
        segment=segment,
        vast_variabel_dynamisch=contract_type,
        bottom=amount,
        postcode=entry.data.get("postcode", "2000"),
        show_prices="yes",
    )

    _LOGGER.info("Adding top contracts to database")

    for i, row in enumerate(data):
        add_top_contract(
            i + 1,
            entry.entry_id,
            row["energietype"],
            row["vast_variabel_dynamisch"],
            row["segment"],
            row["handelsnaam"],
            row["productnaam"],
            row["prijsonderdeel"],
        )
    _LOGGER.info("Top contracts added")
