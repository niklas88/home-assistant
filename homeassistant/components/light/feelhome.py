"""
Support for Feel@Home DIY Devices
"""
import logging
import socket
from struct import pack, unpack

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_EFFECT_LIST, ATTR_EFFECT,
    SUPPORT_RGB_COLOR, SUPPORT_EFFECT,
    Light, PLATFORM_SCHEMA)
from homeassistant.const import CONF_NAME, CONF_IP_ADDRESS, CONF_PORT, CONF_DEVICE, CONF_TYPE

_LOGGER = logging.getLogger(__name__)

SUPPORT_FEELHOMEDIM = (SUPPORT_BRIGHTNESS | SUPPORT_EFFECT)
SUPPORT_FEELHOMERGB = (SUPPORT_BRIGHTNESS | SUPPORT_RGB_COLOR | SUPPORT_EFFECT)

EFFECT_MAP_POWER = {
        'static' : (0x50, 0x03)
}

EFFECT_MAP_DIM = dict(EFFECT_MAP_POWER)
EFFECT_MAP_DIM.update({
        'fading' : (0x44, 0x04),
        'strobe' : (0x44, 0x05)
})

EFFECT_MAP_COLOR = dict(EFFECT_MAP_DIM)
EFFECT_MAP_COLOR.update({
        'colorwheel' : (0x43, 0x02),
        'sunrise' : (0x43, 0x03)
})

EFFECT_MAP_STRIPE = dict(EFFECT_MAP_COLOR)
EFFECT_MAP_STRIPE.update({
        'randompixelunicolorfade' : (0x53, 0x04),
        'randompixelrandomcolorfade' : (0x53, 0x05),
        'rainbow' : (0x53, 0x06),
        'fire' : (0x53, 0x07)
})

EFFECT_MAP_MATRIX = dict(EFFECT_MAP_COLOR)
EFFECT_MAP_MATRIX.update({
        'heart' : (0x4d, 0x00),
})


EFFECT_MAP_CLOCK = dict(EFFECT_MAP_COLOR)
EFFECT_MAP_CLOCK.update({
        'clock' : (0x54, 0x00)
})

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
    
    if (devicetype == "PowerLight"):
      add_devices([FeelHomePowerLight(name, ip, port, devicenum)])    
    elif (devicetype == "DimLight"):
      add_devices([FeelHomeDimLight(name, ip, port, devicenum)])
    elif (devicetype == "RGBLight"):
      add_devices([FeelHomeRGBLight(name, ip, port, devicenum)])
    elif (devicetype == "StripeLight"):
      add_devices([FeelHomeStripeLight(name, ip, port, devicenum)])
    elif (devicetype == "MatrixLight"):
      add_devices([FeelHomeMatrixLight(name, ip, port, devicenum)])
    elif (devicetype == "WordClockLight"):
      add_devices([FeelHomeWordClockLight(name, ip, port, devicenum)])
class FeelHomePowerLight(Light):
    """Representation of a Feel@Home Power Light."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Light.

        Default brightness and white color.
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
        """Return the display name of this light."""
        return self._name

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
        return False

    def turn_on(self, **kwargs):
        """Instruct the light to turn on and set correct brightness & color."""
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

class FeelHomeDimLight(FeelHomePowerLight):
    """Representation of a Feel@Home Dim Light."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Light.

        Default brightness and white color.
        """
        FeelHomePowerLight.__init__(self,name,ip,port,devicenum)
        self._brightness = 255
        self._effect = 'static'
        self._effect_map = EFFECT_MAP_DIM


    @property
    def brightness(self):
        """Read back the brightness of the light.

        Returns integer in the range of 1-255.
        """
        return self._brightness

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_FEELHOMEDIM

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return list(self._effect_map.keys())

    @property
    def effect(self):
        """Return the current effect."""
        return self._effect

    def set_brightness(self, brightness):
        _LOGGER.info('setting brightness seqnum: {}, ip: {}, port: {}, devicenum: {}'.format(
            self._seqnum, self._ip, self._port, self._devicenum))
        self._brightness = brightness
        MSG_FMT = '>BBBBB'
        msg = pack(MSG_FMT, self._seqnum, self._devicenum, 0x44, 0x00, brightness)
        self._sock.sendto(msg, (self._ip, self._port))
        self._seqnum = (self._seqnum+1)%256

    def set_effect(self, effect):
        _LOGGER.info('effect: {} requested'.format(effect))
        self._effect = effect
        effect_group, effect_num = self._effect_map[self._effect]
        MSG_FMT = '>BBBB'
        msg = pack(MSG_FMT, self._seqnum, self._devicenum, effect_group, effect_num)
        self._sock.sendto(msg, (self._ip, self._port))
        self._seqnum = (self._seqnum+1)%256

    def turn_on(self, **kwargs):
        """Instruct the light to turn on and set correct brightness & color."""
        if ATTR_BRIGHTNESS in kwargs:
            self.set_brightness(kwargs[ATTR_BRIGHTNESS])
        if ATTR_EFFECT in kwargs:
            self.set_effect(kwargs[ATTR_EFFECT])
        super().turn_on(**kwargs)

class FeelHomeRGBLight(FeelHomeDimLight):
    """Representation of a Feel@Home RGB Light."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Light.

        Default brightness and white color.
        """
        FeelHomeDimLight.__init__(self,name,ip,port,devicenum)
        self._rgb_color = [255, 255, 255]
        self._effect_map = EFFECT_MAP_COLOR

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
        super().turn_on(**kwargs)

class FeelHomeStripeLight(FeelHomeRGBLight):
    """Representation of a Feel@Home RGB Light."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Light.

        """
        FeelHomeRGBLight.__init__(self,name,ip,port,devicenum)
        self._rgb_color = [255, 255, 255]
        self._effect_map = EFFECT_MAP_STRIPE 


class FeelHomeMatrixLight(FeelHomeStripeLight):
    """Representation of a Feel@Home RGB Light."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Light.

        """
        FeelHomeStripeLight.__init__(self,name,ip,port,devicenum)
        self._effect_map = EFFECT_MAP_MATRIX 

class FeelHomeWordClockLight(FeelHomeMatrixLight):
    """Representation of a Feel@Home RGB Light."""

    def __init__(self, name, ip, port, devicenum):
        """Initialize a Feel@Home Light.

        """
        FeelHomeMatrixLight.__init__(self,name,ip,port,devicenum)
        self._effect_map = EFFECT_MAP_MATRIX
