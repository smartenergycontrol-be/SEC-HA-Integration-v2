import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, SENSORS_PATH

import logging
import json
import os

_LOGGER: logging.Logger = logging.getLogger(__package__)
logging.getLogger(DOMAIN).setLevel(logging.INFO)


@config_entries.HANDLERS.register(DOMAIN)
class ExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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
            description_placeholders={
                "api_key": "Enter your api key",
                "zip_code": "Enter your zip code",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ExampleOptionsFlow(config_entry)