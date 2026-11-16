"""Cliente asíncrono para comunicación con ELM327 OBD-II WiFi."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .const import (
    KEY_CONNECTION_STATE,
    KEY_ONLINE,
    OBD_COMMANDS,
    STATE_ADAPTER_ONLY,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
)

_LOGGER = logging.getLogger(__name__)

# Respuestas del ELM327 que indican que la ECU no respondió
_NO_DATA_MARKERS = (
    "NO DATA",
    "ERROR",
    "UNABLE TO CONNECT",
    "STOPPED",
    "SEARCHING",
    "?",
)

_INIT_COMMANDS = (
    ("ATZ", "Reset"),
    ("ATE0", "Echo off"),
    ("ATL0", "Linefeeds off"),
    ("ATS0", "Spaces off"),
    ("ATH0", "Headers off"),
    ("ATSP0", "Protocolo automático"),
)


class Elm327Error(Exception):
    """Error de comunicación con el adaptador."""


class Elm327Client:
    """Cliente para comunicar con un ELM327 OBD-II WiFi."""

    def __init__(self, host: str, port: int, timeout: float = 5) -> None:
        """Inicializar cliente."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._initialized = False
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        """Indica si hay un socket abierto con el adaptador."""
        return self._writer is not None and not self._writer.is_closing()

    async def async_connect(self) -> None:
        """Abrir conexión TCP con el adaptador."""
        _LOGGER.debug("Conectando a ELM327 en %s:%s", self.host, self.port)
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), self.timeout
            )
        except (OSError, TimeoutError) as err:
            await self.async_disconnect()
            raise Elm327Error(f"No se pudo conectar a {self.host}:{self.port}: {err}") from err
        self._initialized = False
        _LOGGER.debug("Conectado a ELM327 en %s:%s", self.host, self.port)

    async def async_disconnect(self) -> None:
        """Cerrar conexión."""
        writer = self._writer
        self._reader = None
        self._writer = None
        self._initialized = False
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass

    async def _async_send(self, command: str, timeout: float | None = None) -> str:
        """Enviar un comando y devolver la respuesta (sin el prompt '>')."""
        if not self.connected:
            await self.async_connect()
        assert self._reader is not None and self._writer is not None
        try:
            self._writer.write(f"{command}\r".encode())
            await self._writer.drain()
            raw = await asyncio.wait_for(
                self._reader.readuntil(b">"), timeout or self.timeout
            )
        except (OSError, TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError) as err:
            await self.async_disconnect()
            raise Elm327Error(f"Error enviando {command}: {err}") from err
        return raw.decode(errors="ignore").replace(">", "").strip()

    async def _async_initialize(self) -> None:
        """Inicializar el ELM327 (una vez por conexión)."""
        if self._initialized and self.connected:
            return
        _LOGGER.debug("Inicializando ELM327")
        for cmd, desc in _INIT_COMMANDS:
            response = await self._async_send(cmd, timeout=self.timeout * 2)
            _LOGGER.debug("Init %s (%s): %s", cmd, desc, response)
            await asyncio.sleep(0.2)
        self._initialized = True

    @staticmethod
    def _extract_data(command: str, response: str) -> bytes | None:
        """Obtener los bytes de datos de una respuesta modo 01."""
        expected = "4" + command[1:]  # "010C" -> "410C"
        for line in response.upper().replace("\n", "\r").split("\r"):
            # Ignorar líneas informativas o de error ("SEARCHING...", "NO DATA", ...)
            if not line or any(marker in line for marker in _NO_DATA_MARKERS):
                continue
            line = line.replace(" ", "").strip()
            idx = line.find(expected)
            if idx == -1:
                continue
            payload = line[idx + len(expected):]
            try:
                return bytes.fromhex(payload[: len(payload) // 2 * 2])
            except ValueError:
                continue
        return None

    @staticmethod
    def _decode(command: str, data: bytes) -> float | None:
        """Convertir bytes de datos al valor físico."""
        if command == "010C" and len(data) >= 2:  # RPM
            return (data[0] * 256 + data[1]) / 4
        if command == "010D" and len(data) >= 1:  # Velocidad
            return float(data[0])
        if command in ("0111", "012F") and len(data) >= 1:  # Acelerador / combustible
            return data[0] * 100 / 255
        if command == "0133" and len(data) >= 1:  # Presión barométrica
            return float(data[0])
        if command == "0146" and len(data) >= 1:  # Temperatura ambiente
            return float(data[0] - 40)
        if command == "0142" and len(data) >= 2:  # Voltaje módulo de control
            return (data[0] * 256 + data[1]) / 1000
        return None

    async def async_get_all_data(self) -> dict[str, Any]:
        """Leer todos los PIDs.

        Nunca lanza excepción: devuelve el estado de conexión y los valores
        que se pudieron leer (None para los que no respondieron).
        """
        data: dict[str, Any] = dict.fromkeys(OBD_COMMANDS)
        async with self._lock:
            try:
                await self._async_initialize()
                for key, command in OBD_COMMANDS.items():
                    response = await self._async_send(command)
                    raw = self._extract_data(command, response)
                    data[key] = self._decode(command, raw) if raw is not None else None
                    _LOGGER.debug("%s (%s): %s -> %s", key, command, response, data[key])
                    await asyncio.sleep(0.05)
            except Elm327Error as err:
                _LOGGER.debug("ELM327 no disponible: %s", err)
                data[KEY_CONNECTION_STATE] = STATE_DISCONNECTED
                data[KEY_ONLINE] = False
                return data

        online = any(data[key] is not None for key in OBD_COMMANDS)
        data[KEY_ONLINE] = online
        data[KEY_CONNECTION_STATE] = STATE_CONNECTED if online else STATE_ADAPTER_ONLY
        return data
