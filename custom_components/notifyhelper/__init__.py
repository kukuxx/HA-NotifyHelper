from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .notificationhelper import NotificationHelper

DOMAIN = "notifyhelper"

CONF_DEVICES = "devices"

DEVICE_ID = vol.Match(r"^mobile_app_.*$")

CONFIG_SCHEMA = vol.Schema({
    DOMAIN:
    vol.Schema({
        vol.Required(CONF_DEVICES): vol.Schema([DEVICE_ID]),
    })
},
                           extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:

    config = CONFIG_SCHEMA(config)
    helper = hass.data[DOMAIN] = NotificationHelper(hass, config)
    await helper.start()

    async def service_send(call: ServiceCall):
        """Service to send a message."""
        await helper.send_notification(call.data)

    async def service_read(call: ServiceCall):
        """Service to read a message."""
        await helper.read(call.data)

    hass.services.async_register(DOMAIN, "send", service_send)
    hass.services.async_register(DOMAIN, "read", service_read)

    return True
