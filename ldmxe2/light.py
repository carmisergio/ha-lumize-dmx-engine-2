"""Lumize DMX Engine 2 Light Platform"""
from __future__ import annotations

from typing import Any

import logging

import voluptuous as vol


# Home Aassistant imports
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME
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

# Local imports
from .ldmxe2 import SendError, LumizeDMXEngine2, LumizeDMXEngine2Light
from .const import LDMXE2_INSTANCE, CONF_CHANNEL, LDMXE2_ENTITIES


# Get logger for this file's name
_LOGGER = logging.getLogger(__name__)

# Define platform schema
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_CHANNEL): cv.positive_int,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    _: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Lumize DMX Engine 2 Light platform."""

    # Get config parameters
    name: cv.string = config[CONF_NAME]
    channel: cv.positive_int = config[CONF_CHANNEL]

    # Add devices
    _LOGGER.debug("Setting up light %s, channel: %d", name, channel)

    # Check that the platform has been setup
    if not LDMXE2_INSTANCE in hass.data:
        return False

    # Get LumizeDMXEngine2 object from hass.data
    ldmxe2: LumizeDMXEngine2 = hass.data[LDMXE2_INSTANCE]

    # Generate entity
    entity = LumizeDMXEngine2LightEntity(name, ldmxe2.get_light_entity(channel))

    # Append entity to local list used for services
    hass.data[LDMXE2_ENTITIES].append(entity)

    # Add light entity
    add_entities([entity])

    return True


class LumizeDMXEngine2LightEntity(LightEntity):
    """Representation of an Lumize DMX Engine 2 Light."""

    def __init__(self, name, ldmxe2_light: LumizeDMXEngine2Light) -> None:
        """Initialize an LumizeDMXEngine2Light"""

        # Light object
        self._ldmxe2_light = ldmxe2_light

        # Entity properties
        self._name = name
        self._attr_unique_id = f"{self._ldmxe2_light.host}-{self._ldmxe2_light.channel}"
        self._attr_supported_features = LightEntityFeature.TRANSITION
        self._attr_supported_color_modes: set[ColorMode] = set()
        self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)

        # State
        self._state = None
        self._brightness = None

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

    async def async_added_to_hass(self) -> None:
        self.schedule_update_ha_state(True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on"""

        # Get turn on parameters
        brightness = kwargs.get(ATTR_BRIGHTNESS, None)
        transition = kwargs.get(ATTR_TRANSITION, None)

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

        try:
            await self._ldmxe2_light.turn_off(transition=transition)
        except SendError:
            pass

    async def async_dim_start(self) -> None:
        """Instruct the light to start dimming"""

        try:
            await self._ldmxe2_light.pushbutton_fade_start()
        except SendError:
            pass

    async def async_dim_stop(self) -> None:
        """Instruct the light to stop dimming"""

        try:
            await self._ldmxe2_light.pushbutton_fade_end()
        except SendError:
            pass

        self.schedule_update_ha_state(True)

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        try:
            response = await self._ldmxe2_light.get_state()

            # Set state variables
            self._state = response[0]
            self._brightness = int(response[1])

        except SendError:
            pass

        # Check if integration is connected to the Engine
        self._attr_available = self._ldmxe2_light.is_available()
