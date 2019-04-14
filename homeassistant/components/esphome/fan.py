"""Support for ESPHome fans."""
import logging
from typing import TYPE_CHECKING, List, Optional

from homeassistant.components.fan import (
    SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, SPEED_OFF, SUPPORT_OSCILLATE,
    SUPPORT_SET_SPEED, FanEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from . import EsphomeEntity, platform_async_setup_entry

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from aioesphomeapi import FanInfo, FanState, FanSpeed  # noqa

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistantType,
                            entry: ConfigEntry, async_add_entities) -> None:
    """Set up ESPHome fans based on a config entry."""
    # pylint: disable=redefined-outer-name
    from aioesphomeapi import FanInfo, FanState  # noqa

    await platform_async_setup_entry(
        hass, entry, async_add_entities,
        component_key='fan',
        info_type=FanInfo, entity_type=EsphomeFan,
        state_type=FanState
    )


def _ha_fan_speed_to_esphome(speed: str) -> 'FanSpeed':
    # pylint: disable=redefined-outer-name
    from aioesphomeapi import FanSpeed  # noqa
    return {
        SPEED_LOW: FanSpeed.LOW,
        SPEED_MEDIUM: FanSpeed.MEDIUM,
        SPEED_HIGH: FanSpeed.HIGH,
    }[speed]


def _esphome_fan_speed_to_ha(speed: 'FanSpeed') -> str:
    # pylint: disable=redefined-outer-name
    from aioesphomeapi import FanSpeed  # noqa
    return {
        FanSpeed.LOW: SPEED_LOW,
        FanSpeed.MEDIUM: SPEED_MEDIUM,
        FanSpeed.HIGH: SPEED_HIGH,
    }[speed]


class EsphomeFan(EsphomeEntity, FanEntity):
    """A fan implementation for ESPHome."""

    @property
    def _static_info(self) -> 'FanInfo':
        return super()._static_info

    @property
    def _state(self) -> Optional['FanState']:
        return super()._state

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if speed == SPEED_OFF:
            await self.async_turn_off()
            return

        await self._client.fan_command(
            self._static_info.key, speed=_ha_fan_speed_to_esphome(speed))

    async def async_turn_on(self, speed: Optional[str] = None,
                            **kwargs) -> None:
        """Turn on the fan."""
        if speed == SPEED_OFF:
            await self.async_turn_off()
            return
        data = {'key': self._static_info.key, 'state': True}
        if speed is not None:
            data['speed'] = _ha_fan_speed_to_esphome(speed)
        await self._client.fan_command(**data)

    # pylint: disable=arguments-differ
    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        await self._client.fan_command(key=self._static_info.key, state=False)

    async def async_oscillate(self, oscillating: bool):
        """Oscillate the fan."""
        await self._client.fan_command(key=self._static_info.key,
                                       oscillating=oscillating)

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the entity is on."""
        if self._state is None:
            return None
        return self._state.state

    @property
    def speed(self) -> Optional[str]:
        """Return the current speed."""
        if self._state is None:
            return None
        if not self._static_info.supports_speed:
            return None
        return _esphome_fan_speed_to_ha(self._state.speed)

    @property
    def oscillating(self) -> None:
        """Return the oscillation state."""
        if self._state is None:
            return None
        if not self._static_info.supports_oscillation:
            return None
        return self._state.oscillating

    @property
    def speed_list(self) -> Optional[List[str]]:
        """Get the list of available speeds."""
        if not self._static_info.supports_speed:
            return None
        return [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        flags = 0
        if self._static_info.supports_oscillation:
            flags |= SUPPORT_OSCILLATE
        if self._static_info.supports_speed:
            flags |= SUPPORT_SET_SPEED
        return flags
