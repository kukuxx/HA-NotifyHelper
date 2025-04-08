from __future__ import annotations

import os
import asyncio
import logging

from copy import deepcopy

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_set_service_schema

from .helper import NotificationHelper
from .websocket import register_ws
from .card import async_setup_frontend, async_del_frontend
from .const import (
    DOMAIN, CONF_IOS_DEVICES, CONF_ANDROID_DEVICES, 
    CONF_ENTRY_NAME, CONF_URL, NOTIFY_DOMAIN, 
    ALL_PERSON_SCHEMA, NOTIFY_PERSON_SCHEMA, READ_SCHEMA, 
    CLEAR_SCHEMA, ALL_PERSON_DESCRIBE, NOTIFY_PERSON_DESCRIBE,
    DATA_PATH, SERVICES_LIST, HELPER, PERSON
)

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=True)  # YAML 配置已棄用

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up global services for NotifyHelper."""
    try:
        os.makedirs(os.path.join(hass.config.config_dir, DATA_PATH), exist_ok=True)

        def make_service_handler(handler_func):
            async def wrapper(call: ServiceCall):
                await handler_func(hass, call)
            return wrapper

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

        await async_setup_frontend(hass)

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
        entry_name = entry.data.get(CONF_ENTRY_NAME)
        url = entry.data.get(CONF_URL, None)
        entry_id = entry.entry_id

        helper = NotificationHelper(hass, entry_id, entry_name, ios_devices, android_devices, url)
        hass.data.setdefault(DOMAIN, {})[entry_id] = {
            HELPER: helper,
            PERSON: entry_name,
        }

        entry.async_on_unload(entry.add_update_listener(update_listener))

        await register_ws(hass, helper, entry_name.split(".")[1])
        await helper.async_start()

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
        hass.data[DOMAIN].pop(entry.entry_id, None)

        return True
    except Exception as e:
        _LOGGER.error(f"async_unload_entry error {e}")
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    dir_path = os.path.join(hass.config.config_dir, DATA_PATH)
    json_path = f"{dir_path}/{entry.entry_id}.json"
    pkl_path = f"{dir_path}/{entry.entry_id}.pkl"
    if os.path.exists(json_path):
        os.remove(json_path)
        _LOGGER.debug(f"Removed file: {entry.entry_id}.json")
    if os.path.exists(pkl_path):
        os.remove(pkl_path)
        _LOGGER.debug(f"Removed file: {entry.entry_id}.pkl")

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
        _LOGGER.debug(f"Input data: {call.data}")

    tasks = [
        v[HELPER].async_send(deepcopy(call.data))
        for v in hass.data[DOMAIN].values()
    ]
    await asyncio.gather(*tasks)


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
        if len(targets) > 1:
            tasks = [
                v[HELPER].async_send(deepcopy(call.data))
                for v in hass.data[DOMAIN].values()
                if v[PERSON] in targets
            ]
        else:
            tasks = [
                v[HELPER].async_send(call.data)
                for v in hass.data[DOMAIN].values()
                if v[PERSON] in targets
            ]

        await asyncio.gather(*tasks)


async def notification_read(hass, call):
    """Read notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to read notifications.")
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
        tasks = [
            v[HELPER].async_read()
            for v in hass.data[DOMAIN].values()
            if v[PERSON] in targets
        ]
        await asyncio.gather(*tasks)


async def notification_clear(hass, call):
    """Clear notification to entry"""
    if not hass.data.get(DOMAIN):
        _LOGGER.warning("No entries available for NotifyHelper to clear notifications.")
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
        tasks = [
            v[HELPER].async_clear()
            for v in hass.data[DOMAIN].values()
            if v[PERSON] in targets
        ]
        await asyncio.gather(*tasks)