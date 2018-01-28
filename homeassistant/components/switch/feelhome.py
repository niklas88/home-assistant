"""
Support for Feel@Home DIY Devices
"""
import logging
import socket
from struct import pack, unpack

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (SwitchDevice,PLATFORM_SCHEMA)

from homeassistant.const import CONF_NAME, CONF_IP_ADDRESS, CONF_PORT, CONF_DEVICE, CONF_TYPE

_LOGGER = logging.getLogger(__name__)

EFFECT_MAP_POWER = {
        'static' : (0x50, 0x03)
}

DEFAULT_NAME = 'feelhome'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=8080): cv.port,
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_DEVICE): cv.byte,
    vol.Required(CONF_TYPE): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up a Feel@Home Light platform."""

    name = config.get(CONF_NAME)
    ip = config.get(CONF_IP_ADDRESS)
    port = config.get(CONF_PORT)
    devicenum = config.get(CONF_DEVICE)
    devicetype = config.get(CONF_TYPE)
    
    if (devicetype == "PowerDevice"):
      add_devices([FeelHomePowerDevice(name, ip, port, devicenum)])    


class FeelHomePowerDevice(SwitchDevice):
    """Representation of a Feel@Home Power Device."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Power Device.
        """
        self._name = name
        self._ip = ip
        self._port = port
        self._devicenum = devicenum
        self._is_on = False
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._seqnum = 0

    @property
    def name(self):
        """Return the display name of this device."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._is_on

    @property
    def should_poll(self) -> bool:
        """Return if we should poll this device."""
        return False

    @property
    def assumed_state(self) -> bool:
        """Return True if unable to access real state of the entity."""
        return False

    def turn_on(self, **kwargs):
        """Instruct the device to turn on."""
        self._is_on = True
        _LOGGER.info('turning on seqnum: {}, ip: {}, port: {}, devicenum: {}'.format(
            self._seqnum, self._ip, self._port, self._devicenum))
        MSG_FMT = '>BBBBB'
        msg = pack(MSG_FMT, self._seqnum, self._devicenum, 0x50, 0x01, 0x01)
        self._sock.sendto(msg, (self._ip, self._port))
        self._seqnum = (self._seqnum+1)%256
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Instruct the device to turn off."""
        self._is_on = False
        _LOGGER.info('turning off seqnum: {}, ip: {}, port: {}, devicenum: {}'.format(
            self._seqnum, self._ip, self._port, self._devicenum))
        MSG_FMT = '>BBBBB'
        msg = pack(MSG_FMT, self._seqnum, self._devicenum, 0x50, 0x01, 0x00)
        self._sock.sendto(msg, (self._ip, self._port))
        self._seqnum = (self._seqnum+1)%256
        self.schedule_update_ha_state()
        
#    def update(self) -> None:
#        _LOGGER.warn("update called")

