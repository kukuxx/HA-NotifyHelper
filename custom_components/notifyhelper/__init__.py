from __future__ import annotations

import os
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv

from .notificationhelper import NotificationHelper
from .const import DOMAIN, CONF_DEVICES, CONF_ENTRY_NAME

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)  # YAML 配置已棄用

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up global services for NotifyHelper."""
    try:
        notifications_prth = "/config/custom_components/notifyhelper/notifications"
        if not os.path.exists(notifications_prth):
            os.makedirs(notifications_prth)

        async def service_notify_all(call: ServiceCall):
            """Service that sends notification to all entries."""
            await notify_all(hass, call)

        async def service_notify(call: ServiceCall):
            """Service that sends notifications to specific entries."""
            await notify(hass, call)

        async def service_read(call: ServiceCall):
            """Service that reads notifications to specific entries."""
            await notification_read(hass, call)

        hass.services.async_register(DOMAIN, "all", service_notify_all)
        hass.services.async_register(DOMAIN, "notify", service_notify)
        hass.services.async_register(DOMAIN, "read", service_read)

        return True
    except Exception as e:
        _LOGGER.error(f"async_setup error {e}")
        return False


async def notify_all(hass, call):
    """Send notification to all"""
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


async def notify(hass, call):
    """Send notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return

    targets = call.data.get("targets", [])
    if not targets:
        _LOGGER.debug(f"{targets}")
        _LOGGER.error(f"Please specify at least one target")
        return
    elif not isinstance(targets, list):
        _LOGGER.debug(f"{targets}")
        _LOGGER.error("Targets must be a list in YAML format.")
        return
    else:
        for entry_id, entry in hass.data[DOMAIN].items():
            entry_name = entry[1]
            helper = entry[0]
            try:
                if entry_name in targets:
                    _LOGGER.debug(
                        f"Sending notification to entry {entry_id} with data: {call.data}"
                    )
                    helper = entry[0]
                    await helper.send_notification(call.data)
                else:
                    _LOGGER.debug(f"{targets}:{entry_name} not in targets")
            except Exception as e:
                _LOGGER.error(f"Failed to send notification for entry {entry_id}: {e}")


async def notification_read(hass, call):
    """Read notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return

    targets = call.data.get("targets", [])
    if not targets:
        _LOGGER.debug(f"{targets}")
        _LOGGER.error(f"Please specify at least one target")
        return
    elif not isinstance(targets, list):
        _LOGGER.debug(f"{targets}")
        _LOGGER.error("Targets must be a list in YAML format.")
        return
    else:
        for entry_id, entry in hass.data[DOMAIN].items():
            entry_name = entry[1]
            helper = entry[0]
            try:
                if entry_name in targets:
                    _LOGGER.debug(
                        f"Reading notification to entry {entry_id} with data: {call.data}"
                    )
                    await helper.read(call.data)
                else:
                    _LOGGER.debug(f"{targets}:{entry_name} not in targets")
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
        await helper.stop()
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
        hass.services.async_remove(DOMAIN, "all")
        hass.services.async_remove(DOMAIN, "notify")
        hass.services.async_remove(DOMAIN, "read")
        hass.data.pop(DOMAIN)
