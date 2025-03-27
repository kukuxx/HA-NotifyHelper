from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import async_register_command
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, UPDATE_EVENT

_LOGGER = logging.getLogger(__name__)


async def register_ws(hass, helper, name):
    """register websocket"""
    
    @websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/{name}"})
    @websocket_api.ws_require_user()
    @websocket_api.async_response
    @callback
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

        unsubscribe = async_dispatcher_connect(hass, f"{UPDATE_EVENT}_{name}", handle_notifications_update)
        connection.subscriptions[msg["id"]] = unsubscribe
        connection.send_result(msg["id"])
        await helper.trigger()

    async_register_command(
        hass,
        handle_subscribe_updates
    )