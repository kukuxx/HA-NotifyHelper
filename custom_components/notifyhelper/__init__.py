from __future__ import annotations

import os
import logging

from copy import deepcopy

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_set_service_schema

from .notificationhelper import NotificationHelper
from .const import (
    DOMAIN,
    CONF_IOS_DEVICES,
    CONF_ANDROID_DEVICES,
    CONF_ENTRY_NAME,
    SERVICE_DOMAIN,
    ALL_PERSON_SCHEMA,
    NOTIFY_PERSON_SCHEMA,
    READ_SCHEMA,
    SERVICE_DESCRIBE_SCHEMA,
    SERVICES,
)

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=True)  # YAML 配置已棄用

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

        hass.services.async_register(
            SERVICE_DOMAIN, "all_person", service_notify_all, schema=ALL_PERSON_SCHEMA
        )
        hass.services.async_register(
            SERVICE_DOMAIN, "notify_person", service_notify, schema=NOTIFY_PERSON_SCHEMA
        )
        hass.services.async_register(SERVICE_DOMAIN, "read", service_read, schema=READ_SCHEMA)

        for service_name in SERVICES:
            async_set_service_schema(
                hass, SERVICE_DOMAIN, service_name, SERVICE_DESCRIBE_SCHEMA[service_name]
            )

        return True
    except Exception as e:
        _LOGGER.error(f"async_setup error {e}")
        return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NotifyHelper from a config entry."""
    try:
        # 取得裝置配置
        ios_devices = entry.data.get(CONF_IOS_DEVICES, [])
        android_devices = entry.data.get(CONF_ANDROID_DEVICES, [])
        entry_name = entry.data.get(CONF_ENTRY_NAME, "")
        entry_id = entry.entry_id

        helper = NotificationHelper(hass, ios_devices, android_devices, entry_id, entry_name)
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
    json_path = f"/config/custom_components/notifyhelper/notifications/{entry.entry_id}.json"
    pkl_path = f"/config/custom_components/notifyhelper/notifications/{entry.entry_id}.pkl"
    if os.path.exists(json_path):
        os.remove(json_path)
        _LOGGER.debug(f"Removed file: {entry.entry_id}.json")
    if os.path.exists(pkl_path):
        os.remove(pkl_path)
        _LOGGER.debug(f"Removed file: {entry.entry_id}.pkl")

    if not hass.data[DOMAIN]:
        hass.services.async_remove(SERVICE_DOMAIN, "all_person")
        hass.services.async_remove(SERVICE_DOMAIN, "notify_person")
        hass.services.async_remove(SERVICE_DOMAIN, "read")
        hass.data.pop(DOMAIN)


async def notify_all(hass, call):
    """Send notification to all"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return
    else:
        _LOGGER.debug(f"Input data: {call.data}")

    tasks = [
        hass.async_create_task(helper.send_notification(deepcopy(call.data)))
        for entry_id, (helper, entry_name) in hass.data[DOMAIN].items()
    ]


async def notify(hass, call):
    """Send notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return
    else:
        _LOGGER.debug(f"Input data: {call.data}")

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
        _targets = set(targets)
        tasks = [
            hass.async_create_task(helper.send_notification(call.data))
            for entry_id, (helper, entry_name) in hass.data[DOMAIN].items()
            if entry_name in _targets
        ]


async def notification_read(hass, call):
    """Read notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return
    else:
        _LOGGER.debug(f"Input data: {call.data}")

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
        _targets = set(targets)
        tasks = [
            hass.async_create_task(helper.read(call.data))
            for entry_id, (helper, entry_name) in hass.data[DOMAIN].items()
            if entry_name in _targets
        ]
