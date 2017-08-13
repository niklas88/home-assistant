"""
Support for Feel@Home DIY Devices
"""
import logging
import socket
from struct import pack, unpack

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, ATTR_RGB_COLOR, SUPPORT_RGB_COLOR,
    Light, PLATFORM_SCHEMA)
from homeassistant.const import CONF_NAME, CONF_IP_ADDRESS, CONF_PORT, CONF_DEVICE, CONF_TYPE

_LOGGER = logging.getLogger(__name__)

SUPPORT_FEELHOMERGB = (SUPPORT_BRIGHTNESS | SUPPORT_RGB_COLOR)

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

    add_devices([FeelHomeRGBLight(name, ip, port, devicenum)])


class FeelHomeRGBLight(Light):
    """Representation of a Feel@Home RGB Light."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Light.

        Default brightness and white color.
        """
        self._name = name
        self._ip = ip
        self._port = port
        self._devicenum = devicenum
        self._is_on = False
        self._brightness = 255
        self._rgb_color = [255, 255, 255]
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._seqnum = 0

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Read back the brightness of the light.

        Returns integer in the range of 1-255.
        """
        return self._brightness

    @property
    def rgb_color(self):
        """Read back the color of the light.

        Returns [r, g, b] list with values in range of 0-255.
        """
        return self._rgb_color

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_FEELHOMERGB

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._is_on

    @property
    def should_poll(self) -> bool:
        """Return if we should poll this device."""
        return False

    @property
    def assumed_state(self) -> bool:
        """Return True if unable to access real state of the entity."""
        return True

    def set_brightness(self, brightness):
        _LOGGER.info('setting brightness seqnum: {}, ip: {}, port: {}, devicenum: {}'.format(
            self._seqnum, self._ip, self._port, self._devicenum))
        self._brightness = brightness
        MSG_FMT = '>BBBBB'
        msg = pack(MSG_FMT, self._seqnum, self._devicenum, 0x44, 0x00, brightness)
        self._sock.sendto(msg, (self._ip, self._port))
        self._seqnum = (self._seqnum+1)%256

    def set_color(self, color):
        _LOGGER.info('setting brightness seqnum: {}, ip: {}, port: {}, devicenum: {}'.format(
            self._seqnum, self._ip, self._port, self._devicenum))
        self._rgb_color = color
        MSG_FMT = '>BBBBBBB'
        msg = pack(MSG_FMT, self._seqnum, self._devicenum, 0x43, 0x00,
                self._rgb_color[0], self._rgb_color[1], self._rgb_color[2])
        self._sock.sendto(msg, (self._ip, self._port))
        self._seqnum = (self._seqnum+1)%256

    def turn_on(self, **kwargs):
        """Instruct the light to turn on and set correct brightness & color."""
        if ATTR_RGB_COLOR in kwargs:
            self.set_color(kwargs[ATTR_RGB_COLOR])
        if ATTR_BRIGHTNESS in kwargs:
            self.set_brightness(kwargs[ATTR_BRIGHTNESS])
        self._is_on = True
        _LOGGER.info('turning on seqnum: {}, ip: {}, port: {}, devicenum: {}'.format(
            self._seqnum, self._ip, self._port, self._devicenum))
        MSG_FMT = '>BBBBB'
        msg = pack(MSG_FMT, self._seqnum, self._devicenum, 0x50, 0x01, 0x01)
        self._sock.sendto(msg, (self._ip, self._port))
        self._seqnum = (self._seqnum+1)%256
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
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
