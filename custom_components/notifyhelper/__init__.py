from __future__ import annotations

import asyncio
import logging

from copy import deepcopy

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_set_service_schema
from homeassistant.helpers.storage import Store
from homeassistant.loader import async_get_integration

from .helper import CMD, NotificationHelper
from .websocket import register_ws
from .card import async_setup_frontend, async_del_frontend
from .const import (
    DOMAIN, CONF_IOS_DEVICES, CONF_ANDROID_DEVICES, 
    CONF_ENTRY_NAME, CONF_URL, NOTIFY_DOMAIN, 
    ALL_PERSON_SCHEMA, NOTIFY_PERSON_SCHEMA, READ_SCHEMA, 
    CLEAR_SCHEMA, ALL_PERSON_DESCRIBE, NOTIFY_PERSON_DESCRIBE,
    SERVICES_LIST, HELPER, PERSON, HELPER_VER,
)

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=True)  # YAML 配置已棄用

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up global services for NotifyHelper."""
    try:
        def make_service_handler(handler_func):
            async def wrapper(call: ServiceCall):
                await handler_func(hass, call)
            return wrapper
        
        hass.data.setdefault(DOMAIN, {})

        services = [
            (NOTIFY_DOMAIN, "all_person", notify_all, ALL_PERSON_SCHEMA, ALL_PERSON_DESCRIBE),
            (NOTIFY_DOMAIN, "notify_person", notify, NOTIFY_PERSON_SCHEMA, NOTIFY_PERSON_DESCRIBE),
            (DOMAIN, "read", notification_read, READ_SCHEMA, None),
            (DOMAIN, "clear", notification_clear, CLEAR_SCHEMA, None),
        ]

        for domain, name, func, schema, describe in services:
            hass.services.async_register(domain, name, make_service_handler(func), schema=schema)
            if describe:
                async_set_service_schema(hass, domain, name, describe)

        integration = await async_get_integration(hass, DOMAIN)
        integration_ver = str(integration.version) if integration.version else None
        hass.data[DOMAIN][HELPER_VER] = integration_ver
        await async_setup_frontend(hass)
        
        return True
    except Exception as e:
        _LOGGER.error("Failed to setup %s", e)
        return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NotifyHelper from a config entry."""
    try:
        # 取得裝置配置
        ios_devices = entry.data.get(CONF_IOS_DEVICES, [])
        android_devices = entry.data.get(CONF_ANDROID_DEVICES, [])
        entry_name = entry.data.get(CONF_ENTRY_NAME)
        url = entry.data.get(CONF_URL, None)
        entry_id = entry.entry_id

        storage = Store(hass, 1, f"{DOMAIN}/{entry.entry_id}.json")
        helper = NotificationHelper(hass, entry_id, entry_name, ios_devices, 
                                    android_devices, url, storage)
        
        entry.async_on_unload(entry.add_update_listener(update_listener))

        await register_ws(hass, helper, entry_name.split(".")[1])
        await helper.async_initialize()
        entry.async_create_background_task(
            hass,
            helper.async_handle_commands(),
            name=f"{DOMAIN} {entry_name} command handler",
        )
        hass.data[DOMAIN][entry_id] = {
            HELPER: helper,
            PERSON: entry_name,
        }

        return True
    except Exception as e:
        _LOGGER.error("Failed to setup entry %s", e)
        return False


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    try:
        await hass.config_entries.async_reload(entry.entry_id)
    except Exception as e:
        _LOGGER.error("Failed to update entry %s", e)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        await entry_data[HELPER].aclose()

        return True
    except Exception as e:
        _LOGGER.error("Failed to unload entry %s", e)
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    helper = hass.data[DOMAIN][entry.entry_id][HELPER]
    await helper._store.async_remove() 
    _LOGGER.debug("Removed file: %s.json", entry.entry_id)

    if DOMAIN in hass.data and not hass.data[DOMAIN]:
        await async_del_frontend(hass)

        for service_domain, service_name in SERVICES_LIST:
            hass.services.async_remove(service_domain, service_name)
           
        hass.data.pop(DOMAIN)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry."""
    if entry.version > 2:
        # 未來版本無法處理
        return False

    if entry.version < 2:
        # 舊版本更新資料
        data = deepcopy(dict(entry.data))
        for key, value in entry.data.items():
            if key not in (CONF_ENTRY_NAME, CONF_URL, CONF_IOS_DEVICES, CONF_ANDROID_DEVICES):
                data.pop(key)

        data.setdefault(CONF_URL, "")
        data.setdefault(CONF_IOS_DEVICES, [])
        data.setdefault(CONF_ANDROID_DEVICES, [])
        hass.config_entries.async_update_entry(entry, version=2, data=data)
    return True


async def notify_all(hass, call):
    """Send notification to all"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return
    else:
        _LOGGER.debug("Input data: %s", call.data)

    tasks = [
        entry_data[HELPER].async_put((CMD.SEND, deepcopy(call.data)))
        for entry_data in hass.data[DOMAIN].values()
        if isinstance(entry_data, dict) and HELPER in entry_data
    ]
    await asyncio.gather(*tasks)


async def notify(hass, call):
    """Send notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to send notifications.")
        return
    else:
        _LOGGER.debug("Input data: %s", call.data)

    targets = call.data.get("targets", [])
    if not targets:
        _LOGGER.debug("Targets: %s", targets)
        _LOGGER.error("Please specify at least one target")
        return
    elif not isinstance(targets, list):
        _LOGGER.debug("Targets: %s", targets)
        _LOGGER.error("Targets must be a list in YAML format.")
        return
    else:
        if len(targets) > 1:
            tasks = [
                entry_data[HELPER].async_put((CMD.SEND, deepcopy(call.data)))
                for entry_data in hass.data[DOMAIN].values()
                if (
                    isinstance(entry_data, dict) 
                    and HELPER in entry_data
                    and entry_data[PERSON] in targets
                )
            ]
        else:
            tasks = [
                entry_data[HELPER].async_put((CMD.SEND, call.data))
                for entry_data in hass.data[DOMAIN].values()
                if (
                    isinstance(entry_data, dict) 
                    and HELPER in entry_data
                    and entry_data[PERSON] in targets
                )
            ]

        await asyncio.gather(*tasks)


async def notification_read(hass, call):
    """Read notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to read notifications.")
        return
    else:
        _LOGGER.debug("Input data: %s", call.data)

    targets = call.data.get("targets", [])
    if not targets:
        _LOGGER.debug("Targets: %s", targets)
        _LOGGER.error("Please specify at least one target")
        return
    elif not isinstance(targets, list):
        _LOGGER.debug("Targets: %s", targets)
        _LOGGER.error("Targets must be a list in YAML format.")
        return
    else:
        tasks = [
            entry_data[HELPER].async_put((CMD.READ, None))
            for entry_data in hass.data[DOMAIN].values()
            if (
                isinstance(entry_data, dict) 
                and HELPER in entry_data
                and entry_data[PERSON] in targets
            )
        ]
        await asyncio.gather(*tasks)


async def notification_clear(hass, call):
    """Clear notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to clear notifications.")
        return
    else:
        _LOGGER.debug("Input data: %s", call.data)

    targets = call.data.get("targets", [])
    if not targets:
        _LOGGER.debug("Targets: %s", targets)
        _LOGGER.error("Please specify at least one target")
        return
    elif not isinstance(targets, list):
        _LOGGER.debug("Targets: %s", targets)
        _LOGGER.error("Targets must be a list in YAML format.")
        return
    else:
        tasks = [
            entry_data[HELPER].async_put((CMD.CLEAR, None))
            for entry_data in hass.data[DOMAIN].values()
            if (
                isinstance(entry_data, dict) 
                and HELPER in entry_data
                and entry_data[PERSON] in targets
            )
        ]
        await asyncio.gather(*tasks)
