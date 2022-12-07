"""Lumize DVMX Engine 2 Integration"""
from __future__ import annotations

import logging

import voluptuous as vol

from .ldmxe2 import LumizeDMXEngine2

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, Event

DOMAIN = "ldmxe2"
KEY_LDMXE2_INSTANCE = "ldmxe2_instance"

PLATFORMS: list[Platform] = [
    # Platform.LIGHT
]

# Set up Home Assistant logger with this file's name
_LOGGER = logging.getLogger(__name__)

# Config schema definition
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required(CONF_HOST): cv.string, vol.Optional(CONF_PORT): int}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def test_logger(log_function):
    log_function.info("Test logger")


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up LumizeDMXEngine2 from a config entry."""

    conf = config[DOMAIN]
    host = conf[CONF_HOST]
    port = conf[CONF_PORT]

    _LOGGER.info(f"Starting connection to host {host}")

    # Create ldmxe2 instance
    ldmxe2 = LumizeDMXEngine2(host, 8056, _LOGGER.info)

    # Start the connection to engine
    ldmxe2.start()

    # Save instance to be able to use it from platforms
    hass.data[KEY_LDMXE2_INSTANCE] = ldmxe2

    _LOGGER.info("Setup completed!")
    test_logger(_LOGGER)

    return True
