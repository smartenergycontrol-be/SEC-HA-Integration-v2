"""Config flow and options flow."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN
from .db import (
    add_contract,
    add_custom_sensor,
    get_contracts,
    get_custom_sensors,
    remove_contract,
    remove_custom_sensor,
)

_LOGGER = logging.getLogger(__name__)
logging.getLogger(DOMAIN).setLevel(logging.DEBUG)


@config_entries.HANDLERS.register(DOMAIN)
class SecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="sec", data=user_input)

        data_schema = vol.Schema(
            {vol.Required("api_key"): str, vol.Required("zip_code"): str}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SecOptionsFlow(config_entry)


class SecOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.energy_type = None
        self.vast_variabel_dynamisch = None
        self.segment = None
        self.supplier = None
        self.contract = None
        self.price_component = None
        self.jaar = None
        self.maand = None

        self.conf_top_energy_type = None
        self.conf_top_segment = None
        self.conf_top_vast_variabel_dynamisch = None
        self.conf_top_contracts_limit = None

    async def async_step_init(self, user_input=None):
        """Handle the initial step of the options flow."""
        if user_input is not None:
            action = user_input["action"]
            if action == "Add contract":
                return await self.async_step_selection()
            if action == "Set contract id":
                return await self.async_step_assign_custom_name()
            if action == "Remove contract":
                return await self.async_step_remove_contract()
            if action == "Remove custom sensor":
                return await self.async_step_remove_custom_sensor()
            if action == "Configure top contracts":
                return await self.async_step_configure_top_contracts()

        data_schema = vol.Schema(
            {
                vol.Required("action"): vol.In(
                    [
                        "Add contract",
                        "Set contract id",
                        "Remove contract",
                        "Remove custom sensor",
                        "Configure top contracts",
                    ]
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )

    async def async_step_selection(self, user_input=None):
        """Handle the selection of energy type, contract type, and segment."""
        if user_input is not None:
            self.energy_type = user_input["energy_type"]
            self.vast_variabel_dynamisch = user_input["vast_variabel_dynamisch"]
            self.segment = user_input["segment"]
            # _LOGGER.debug(
            #     f"Selection: Energy Type: {self.energy_type}, "
            #     f"Contract Type: {self.vast_variabel_dynamisch}, Segment: {self.segment}"
            # )
            if self.vast_variabel_dynamisch == "Vast":
                return await self.async_step_time_selection()

            return await self.async_step_supplier_selection()

        data_schema = vol.Schema(
            {
                vol.Required("energy_type"): vol.In(["Elektriciteit", "Gas"]),
                vol.Required("vast_variabel_dynamisch"): vol.In(
                    ["Dynamisch", "Variabel", "Vast"]
                ),
                vol.Required("segment"): vol.In(["Woning", "Onderneming"]),
            }
        )

        return self.async_show_form(
            step_id="selection",
            data_schema=data_schema,
            description_placeholders={"selection_help": "Select the required options"},
        )

    async def async_step_time_selection(self, user_input=None):
        """Handle the time selection (year and month) for 'Vast' contracts."""
        if user_input is not None:
            self.jaar = user_input["jaar"]
            self.maand = user_input["maand"]
            return await self.async_step_supplier_selection()

        data_schema = vol.Schema(
            {
                vol.Required("jaar"): vol.In([str(year) for year in range(2022, 2025)]),
                vol.Required("maand"): vol.In(
                    [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ]
                ),
            }
        )

        return self.async_show_form(
            step_id="time_selection",
            data_schema=data_schema,
            description_placeholders={
                "time_help": "Select the year and month for the 'Vast' contract."
            },
        )

    async def async_step_supplier_selection(self, user_input=None):
        """Handle the selection of supplier."""
        if user_input is not None:
            self.supplier = user_input["selected_supplier"]
            _LOGGER.debug(f"Selected Supplier: {self.supplier}")
            return await self.async_step_contract_selection()

        api = self.hass.data[DOMAIN][self.config_entry.entry_id]

        if not await api.authenticate():
            _LOGGER.error("API Authentication Failed")
            return self.async_abort(reason="api_data_error")

        prijsonderdelen_list = await api.get_prijsonderdelen(
            jaar=self.jaar,
            maand=self.maand,
            energietype=self.energy_type,
            vast_variabel_dynamisch=self.vast_variabel_dynamisch,
            segment=self.segment,
        )

        if prijsonderdelen_list is None:
            _LOGGER.error("No data returned from API for supplier selection")
            return self.async_abort(reason="api_data_error")

        _LOGGER.debug(f"Prijsonderdelen list received: {prijsonderdelen_list}")

        filtered_suppliers = list(
            {p.get("handelsnaam") for p in prijsonderdelen_list if p.get("handelsnaam")}
        )

        if not filtered_suppliers:
            _LOGGER.warning("No suppliers found with the selected filters")
            return self.async_abort(reason="no_suppliers_found")

        _LOGGER.debug(f"Filtered suppliers: {filtered_suppliers}")

        data_schema = vol.Schema(
            {vol.Required("selected_supplier"): vol.In(filtered_suppliers)}
        )

        return self.async_show_form(
            step_id="supplier_selection",
            data_schema=data_schema,
            description_placeholders={
                "suppliers_help": "Select a supplier from the list"
            },
        )

    async def async_step_contract_selection(self, user_input=None):
        """Handle the selection of a contract."""
        if user_input is not None:
            self.contract = user_input["selected_contract"]
            _LOGGER.debug(f"Selected Contract: {self.contract}")
            return await self.async_step_price_component_selection()

        api = self.hass.data[DOMAIN][self.config_entry.entry_id]

        prijsonderdelen_list = await api.get_prijsonderdelen(
            jaar=self.jaar,
            maand=self.maand,
            energietype=self.energy_type,
            vast_variabel_dynamisch=self.vast_variabel_dynamisch,
            segment=self.segment,
            handelsnaam=self.supplier,
        )

        if prijsonderdelen_list is None:
            _LOGGER.error("No data returned from API for contract selection")
            return self.async_abort(reason="api_data_error")

        _LOGGER.debug(f"Prijsonderdelen list received: {prijsonderdelen_list}")

        filtered_contracts = list(
            {p.get("productnaam") for p in prijsonderdelen_list if p.get("productnaam")}
        )

        if not filtered_contracts:
            _LOGGER.warning("No contracts found for the selected supplier")
            return self.async_abort(reason="no_contracts_found")

        _LOGGER.debug(f"Filtered contracts: {filtered_contracts}")

        data_schema = vol.Schema(
            {vol.Required("selected_contract"): vol.In(filtered_contracts)}
        )

        return self.async_show_form(
            step_id="contract_selection",
            data_schema=data_schema,
            description_placeholders={
                "contracts_help": "Select a contract from the list"
            },
        )

    async def async_step_price_component_selection(self, user_input=None):
        """Handle the selection of a price component."""
        if user_input is not None:
            add_contract(
                self.config_entry.entry_id,
                self.energy_type,
                self.vast_variabel_dynamisch,
                self.segment,
                self.supplier,
                self.contract,
                user_input["selected_price_component"],
                self.maand,
                self.jaar,
            )

            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="Contract Added", data=None)

        api = self.hass.data[DOMAIN][self.config_entry.entry_id]

        prijsonderdelen_list = await api.get_prijsonderdelen(
            jaar=self.jaar,
            maand=self.maand,
            energietype=self.energy_type,
            vast_variabel_dynamisch=self.vast_variabel_dynamisch,
            segment=self.segment,
            handelsnaam=self.supplier,
            productnaam=self.contract,
        )

        if prijsonderdelen_list is None:
            _LOGGER.error("No data returned from API for price component selection")
            return self.async_abort(reason="api_data_error")

        _LOGGER.debug(f"Prijsonderdelen list received: {prijsonderdelen_list}")

        filtered_price_components = list(
            {
                p.get("prijsonderdeel")
                for p in prijsonderdelen_list
                if p.get("prijsonderdeel")
            }
        )

        if not filtered_price_components:
            _LOGGER.warning("No price components found for the selected contract")
            return self.async_abort(reason="no_price_components_found")

        data_schema = vol.Schema(
            {
                vol.Required("selected_price_component"): vol.In(
                    filtered_price_components
                )
            }
        )

        return self.async_show_form(
            step_id="price_component_selection",
            data_schema=data_schema,
            description_placeholders={
                "price_components_help": "Select a price component from the list"
            },
        )

    async def async_step_assign_custom_name(self, user_input=None):
        """Assign a custom name to a sensor."""
        if user_input is not None:
            custom_name = user_input["custom_sensor_name"]
            if user_input["use_prefix"]:
                custom_name = f"{user_input['prefix']}{custom_name}"

            add_custom_sensor(
                self.config_entry.entry_id,
                user_input["sensor_id"],
                custom_name,
            )

            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(
                title=f"Created sensor.{custom_name}\nCreated sensor.{custom_name}_afname\nCreated sensor.{custom_name}_injectie",
                data={},
            )

        sensor_options = {
            sensor[10]: sensor[10].strip("sensor.sec_").replace("_", " ").title()
            for sensor in get_contracts(self.config_entry.entry_id)
        }

        data_schema = vol.Schema(
            {
                vol.Required("sensor_id"): vol.In(sensor_options),
                vol.Required("custom_sensor_name"): str,
                vol.Required("use_prefix", default=True): bool,
                vol.Optional("prefix", default="sec_"): str,
            }
        )

        return self.async_show_form(
            step_id="assign_custom_name",
            data_schema=data_schema,
            description_placeholders={
                "prefix_help": "Prefix will be applied if 'Use Prefix' is enabled."
            },
        )

    async def async_step_remove_contract(self, user_input=None):
        """Remove an existing contract sensor."""
        if user_input is not None:
            remove_contract(user_input["sensor_id"])

            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(
                title="Removed contract",
                data={},
            )

        sensor_options = {
            sensor[10]: sensor[10].strip("sensor.sec_").replace("_", " ").title()
            for sensor in get_contracts(self.config_entry.entry_id)
        }

        data_schema = vol.Schema(
            {
                vol.Required("sensor_id"): vol.In(sensor_options),
            }
        )

        return self.async_show_form(
            step_id="remove_contract",
            data_schema=data_schema,
            description_placeholders={},
        )

    async def async_step_remove_custom_sensor(self, user_input=None):
        """Remove an existing custom sensor."""
        if user_input is not None:
            remove_custom_sensor(user_input["sensor_name"])

            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(
                title="Removed contract",
                data={},
            )

        sensor_options = {
            sensor[3]: sensor[3].strip("sensor.sec_").replace("_", " ").title()
            for sensor in get_custom_sensors(self.config_entry.entry_id)
        }

        data_schema = vol.Schema(
            {
                vol.Required("sensor_name"): vol.In(sensor_options),
            }
        )

        return self.async_show_form(
            step_id="remove_custom_sensor",
            data_schema=data_schema,
            description_placeholders={},
        )

    async def async_step_configure_top_contracts(self, user_input=None):
        """Handle the configuration of top contracts."""
        if user_input is not None:
            self.conf_top_energy_type = user_input["conf_top_energy_type"]
            self.conf_top_segment = user_input["conf_top_segment"]
            self.conf_top_vast_variabel_dynamisch = user_input["conf_top_contract_type"]
            self.conf_top_contracts_limit = user_input["conf_top_contracts_limit"]

            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="Top Contracts Configured", data={})

        data_schema = vol.Schema(
            {
                vol.Required("conf_top_energy_type", default="All"): vol.In(
                    ["Elektriciteit", "Gas", "All"]
                ),
                vol.Required("conf_top_segment", default="All"): vol.In(
                    ["Woning", "Onderneming", "All"]
                ),
                vol.Required("conf_top_contract_type", default="All"): vol.In(
                    ["Dynamisch", "Variabel", "Vast", "All"]
                ),
                vol.Required("conf_top_contracts_limit", default=5): vol.Coerce(int),
            }
        )

        return self.async_show_form(
            step_id="configure_top_contracts",
            data_schema=data_schema,
            description_placeholders={
                "description": "Configure top contracts filter and limit"
            },
        )
