"""Lumize DMX Engine 2 Light Platform"""
from __future__ import annotations

from typing import Any

import logging

import voluptuous as vol

from pprint import pformat

from .ldmxe2 import SendError

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from homeassistant.components.light import (
    PLATFORM_SCHEMA,
    ATTR_BRIGHTNESS,
    ATTR_TRANSITION,
    LightEntity,
    LightEntityFeature,
    ColorMode,
)

_LOGGER = logging.getLogger("ldmxe2")

# Validation of the user's configuration
CONF_CHANNEL = "channel"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_CHANNEL): cv.positive_int,
    }
)

DOMAIN = "ldmxe2"
KEY_LDMXE2_INSTANCE = "ldmxe2_instance"


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Lumize DMX Engine 2 Light platform."""

    # Get config
    name = config[CONF_NAME]
    channel = config[CONF_CHANNEL]

    # Add devices
    _LOGGER.info(f'Setting up light "{name}", channel: {channel}')

    # Check that the platform has been setup
    # if(!(KEY_LDMXE2_INSTANCE in  hass.data)):
    #     return False

    ldmxe2 = hass.data[KEY_LDMXE2_INSTANCE]
    _LOGGER.info(KEY_LDMXE2_INSTANCE)
    _LOGGER.info(hass.data[KEY_LDMXE2_INSTANCE])

    add_entities([LumizeDMXEngine2LightEntity(name, ldmxe2.get_light_entity(channel))])

    return True


class LumizeDMXEngine2LightEntity(LightEntity):
    """Representation of an Lumize DMX Engine 2 Light."""

    def __init__(self, name, ldmxe2_light) -> None:
        """Initialize an LumizeDMXEngine2Light"""
        # _LOGGER.info(pformat(light))
        self._ldmxe2_light = ldmxe2_light
        self._name = name
        self._state = None
        self._brightness = None

        self._attr_unique_id = f"light-ldmxe2-{name.strip()}"

        self._attr_supported_features = LightEntityFeature.TRANSITION

        self._attr_supported_color_modes: set[ColorMode] = set()
        self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on"""

        # Get turn on parameters
        brightness = kwargs.get(ATTR_BRIGHTNESS, None)
        transition = kwargs.get(ATTR_TRANSITION, None)
        _LOGGER.info(
            f"Light turn on, brightness: {brightness}, transition: {transition}"
        )

        try:
            await self._ldmxe2_light.turn_on(
                brightness=brightness, transition=transition
            )
        except SendError:
            pass

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""

        # Get turn off parameters
        transition = kwargs.get(ATTR_TRANSITION, None)

        _LOGGER.info(f"Light turn off, transition: {transition}")

        try:
            await self._ldmxe2_light.turn_off(transition=transition)
        except SendError:
            pass

    async def async_update(self) -> None:
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            response = await self._ldmxe2_light.get_state()
            self._state = response[0]
            self._brightness = int(response[1])
            _LOGGER.info(f"State {self._state}, brightness: {self._brightness}")
        except SendError:
            _LOGGER.info(f"Get state error")
            pass

        self._attr_available = self._ldmxe2_light.is_available()
