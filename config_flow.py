"""Config flow para ELM327 OBD-II WiFi."""
import logging
import socket
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validar la configuración del usuario."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    
    try:
        # Probar conexión TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        await hass.async_add_executor_job(sock.connect, (host, port))
        sock.close()
        
        return {"title": f"ELM327 OBD-II ({host}:{port})"}
    except Exception as e:
        _LOGGER.error(f"Error conectando a {host}:{port}: {e}")
        raise CannotConnect


class Elm327ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Manejador del config flow para ELM327 OBD-II."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Manejar el paso inicial."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error inesperado")
            errors["base"] = "unknown"
        else:
            # Crear entrada única basada en host
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error para indicar que no se puede conectar."""