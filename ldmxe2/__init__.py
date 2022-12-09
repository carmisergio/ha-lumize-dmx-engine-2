"""Lumize DMX Engine 2 Integration"""

from __future__ import annotations

import logging

import voluptuous as vol

# Home Assistant imports
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant

# Local imports
from .ldmxe2 import LumizeDMXEngine2
from .const import (
    DOMAIN,
    LDMXE2_INSTANCE,
    CONF_KEEP_ALIVE,
    DEFAULT_PORT,
    DEFAULT_KEEP_ALIVE,
)


# Define platforms the integration provides
PLATFORMS: list[Platform] = [Platform.LIGHT]

# Set up Home Assistant logger with this file's name
_LOGGER = logging.getLogger(__name__)

# Config schema definition
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.positive_int,
                vol.Optional(
                    CONF_KEEP_ALIVE, default=DEFAULT_KEEP_ALIVE
                ): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up Lumize DMX Engine 2 from config"""

    # Get configuration parameters
    conf = config[DOMAIN]
    host = conf[CONF_HOST]
    port = conf[CONF_PORT]
    keep_alive = conf[CONF_KEEP_ALIVE]

    _LOGGER.debug("Starting connection to host %s", host)

    # Create ldmxe2 instance
    ldmxe2 = LumizeDMXEngine2(host, int(port), _LOGGER.debug, keep_alive)

    # Start the connection to engine
    ldmxe2.start()

    # Save instance to be able to use it from platforms
    hass.data[LDMXE2_INSTANCE] = ldmxe2

    _LOGGER.info("Setup completed, host: %s", host)

    return True
