from __future__ import annotations

import os
import logging
import glob

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv

from .notificationhelper import NotificationHelper
from .const import DOMAIN, CONF_DEVICES, CONF_ENTRY_NAME

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)  # YAML 配置已棄用

_LOGGER = logging.getLogger(__name__)
_RELOAD = False


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up global services for NotifyHelper."""

    try:
        notifications_prth = "/config/custom_components/notifyhelper/notifications"
        if not os.path.exists(notifications_prth):
            os.makedirs(notifications_prth)

        async def service_send_all(call: ServiceCall):
            """Service to send a notification to all entries."""
            await send_all_notify(hass, call)

        hass.services.async_register(DOMAIN, "send_all", service_send_all)

        return True
    except Exception as e:
        _LOGGER.error(f"async_setup error {e}")
        return False


async def send_all_notify(hass, call):
    """send a notification to all"""

    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return

    for entry_id, entry in hass.data[DOMAIN].items():
        try:
            _LOGGER.debug(f"Sending notification to entry {entry_id} with data: {call.data}")
            helper = entry[0]
            await helper.send_notification(call.data)
        except Exception as e:
            _LOGGER.error(f"Failed to send notification for entry {entry_id}: {e}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NotifyHelper from a config entry."""

    try:
        # 取得裝置配置
        devices = entry.data.get(CONF_DEVICES, [])
        entry_name = entry.data.get(CONF_ENTRY_NAME, "")
        entry_id = entry.entry_id

        helper = NotificationHelper(hass, devices, entry_id, entry_name)
        hass.data.setdefault(DOMAIN, {})[entry_id] = [helper, entry_name]
        await helper.start()

        # 註冊服務
        async def service_send(call: ServiceCall):
            """Service to send a message."""
            await helper.send_notification(call.data)

        async def service_read(call: ServiceCall):
            """Service to read a message."""
            await helper.read(call.data)

        hass.services.async_register(DOMAIN, f"send_{entry_name}", service_send)
        hass.services.async_register(DOMAIN, f"read_{entry_name}", service_read)

        entry.async_on_unload(entry.add_update_listener(update_listener))

        return True
    except Exception as e:
        _LOGGER.error(f"async_setup_entry error {e}")
        return False


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""

    try:
        await hass.config_entries.async_reload(entry.entry_id)
    except Exception as e:
        _LOGGER.error(f"update_listener error {e}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    try:
        # 停止 NotificationHelper 刪除sensor
        entry = hass.data[DOMAIN].pop(entry.entry_id)
        helper = entry[0]
        entry_name = entry[1]

        await helper.stop()
        # 註銷服務
        hass.services.async_remove(DOMAIN, f"send_{entry_name}")
        hass.services.async_remove(DOMAIN, f"read_{entry_name}")

        entry = None
        return True
    except Exception as e:
        _LOGGER.error(f"async_unload_entry error {e}")
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""

    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""

    file_path = f"/config/custom_components/notifyhelper/notifications/{entry.entry_id}.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        _LOGGER.info(f"Removed file: {entry.entry_id}.json")

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "send_all")
        hass.data.pop(DOMAIN)
