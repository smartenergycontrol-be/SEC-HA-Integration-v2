import logging

_LOGGER = logging.getLogger(__name__)
INPUT_SELECT_ENTITY_ID = "input_select.selected_sensor"


async def update_input_select(hass, sensors: list):
    """Update the input_select entity with available sensors."""
    # Check if the input_select already exists
    if INPUT_SELECT_ENTITY_ID not in hass.states.async_entity_ids():
        _LOGGER.info(f"Creating input_select {INPUT_SELECT_ENTITY_ID}")
        # If the input_select doesn't exist, create it dynamically
        await hass.services.async_call(
            "input_select",
            "create",
            {
                "entity_id": INPUT_SELECT_ENTITY_ID,
                "name": "Select Sensor",
                "options": sensors,
                "initial": sensors[0] if sensors else "",
            },
            blocking=True,
        )
    else:
        _LOGGER.info(f"Updating input_select {INPUT_SELECT_ENTITY_ID} with new sensors")
        # Update the options of the existing input_select
        await hass.services.async_call(
            "input_select",
            "set_options",
            {
                "entity_id": INPUT_SELECT_ENTITY_ID,
                "options": sensors,
            },
            blocking=True,
        )
