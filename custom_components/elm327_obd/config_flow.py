"""Config flow para ELM327 OBD-II WiFi."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .coordinator import Elm327ConfigEntry

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
    }
)


async def _async_can_connect(host: str, port: int) -> bool:
    """Probar conexión TCP con el adaptador."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), DEFAULT_TIMEOUT
        )
    except (OSError, TimeoutError) as err:
        _LOGGER.debug("Error conectando a %s:%s: %s", host, port, err)
        return False
    writer.close()
    try:
        await writer.wait_closed()
    except OSError:
        pass
    return True


class Elm327ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Manejador del config flow para ELM327 OBD-II."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manejar el paso inicial."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            if await _async_can_connect(host, port):
                return self.async_create_entry(
                    title=f"ELM327 OBD-II ({host}:{port})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Elm327ConfigEntry) -> Elm327OptionsFlow:
        """Obtener el options flow."""
        return Elm327OptionsFlow()


class Elm327OptionsFlow(OptionsFlow):
    """Opciones de ELM327 OBD-II."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Gestionar opciones."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
