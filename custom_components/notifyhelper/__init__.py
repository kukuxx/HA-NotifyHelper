from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv

from .notificationhelper import NotificationHelper
from .const import DOMAIN, CONF_DEVICES

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)  # YAML 配置已棄用


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up NotifyHelper from YAML (deprecated)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NotifyHelper from a config entry."""
    # 取得裝置配置（優先從 entry.options 讀取，如果未設定則從 entry.data 讀取）
    devices = entry.options.get(CONF_DEVICES, entry.data.get(CONF_DEVICES, []))

    helper = NotificationHelper(hass, devices)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = helper
    await helper.start()

    # 註冊服務
    async def service_send(call: ServiceCall):
        """Service to send a message."""
        await helper.send_notification(call.data)

    async def service_read(call: ServiceCall):
        """Service to read a message."""
        await helper.read(call.data)

    hass.services.async_register(DOMAIN, "send", service_send)
    hass.services.async_register(DOMAIN, "read", service_read)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # 停止 NotificationHelper 刪除sensor
    helper: NotificationHelper = hass.data[DOMAIN].pop(entry.entry_id)
    await helper.stop()

    # 註銷服務
    hass.services.async_remove(DOMAIN, "send")
    hass.services.async_remove(DOMAIN, "read")

    return True
