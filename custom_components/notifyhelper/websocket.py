from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.components.websocket_api import (
  decorators,
  async_register_command
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import EVENT

_LOGGER = logging.getLogger(__name__)


@callback
@decorators.websocket_command({
    vol.Required("type"): EVENT,
})
@decorators.async_response
async def handle_subscribe_updates(hass, connection, msg):
    """Handle subscription event listeners"""

    _LOGGER.debug(f"WS subscription successful: {msg}") 

    @callback
    def handle_notifications_update(data: dict):
        connection.send_message({
            "id": msg["id"],
            "type": "event",
            "event": data,
        })
        _LOGGER.debug(f"WS send msg: {data}")

    unsubscribe = async_dispatcher_connect(hass, "update", handle_notifications_update)
    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"])