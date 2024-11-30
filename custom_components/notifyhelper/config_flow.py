import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CONF_DEVICES, CONF_ENTRY_NAME

_LOGGER = logging.getLogger(__name__)


class NotifyHelperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NotifyHelper."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration step."""
        errors = {}

        if user_input is not None:
            # 驗證輸入內容
            if any(
                entry.data.get(CONF_ENTRY_NAME) == user_input[CONF_ENTRY_NAME]
                for entry in self._async_current_entries()
            ):
                errors["base"] = "name_exists"  # 名稱已存在
            elif not user_input[CONF_DEVICES]:
                errors["base"] = "no_device"  # 顯示錯誤提示
            elif any(
                set(user_input[CONF_DEVICES]) & set(entry.data.get(CONF_DEVICES, []))
                for entry in self._async_current_entries()
            ):
                errors["base"] = "devices_conflict"
            else:
                # 保存配置
                return self.async_create_entry(
                    title=user_input[CONF_ENTRY_NAME],
                    data=user_input,
                )

        # 取得所有 notify domain的服務
        notify_services = self.hass.services.async_services().get("notify", {})
        mobile_app_devices = [
            devices for devices in notify_services if devices.startswith("mobile_app")
        ]

        entity_registry = er.async_get(self.hass)
        person_entities = [
            entity.entity_id for entity in entity_registry.entities.values()
            if entity.entity_id.startswith("person.")
        ]

        schema = vol.Schema({
            vol.Required(CONF_ENTRY_NAME):
            vol.In(person_entities),
            vol.Required(CONF_DEVICES, default=[]):
            cv.multi_select(mobile_app_devices)
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return NotifyHelperOptionsFlow(config_entry)


class NotifyHelperOptionsFlow(config_entries.OptionsFlow):
    """Handle options for NotifyHelper."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options for NotifyHelper."""
        errors = {}

        existing_entries = [
            entry for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.entry_id != self.config_entry.entry_id
        ]

        if user_input is not None:
            if any(
                entry.data.get(CONF_ENTRY_NAME) == user_input[CONF_ENTRY_NAME]
                for entry in existing_entries
            ):
                errors["base"] = "name_exists"
            elif not user_input[CONF_DEVICES]:
                errors["base"] = "no_device"
            elif any(
                set(user_input[CONF_DEVICES]) & set(entry.data.get(CONF_DEVICES))
                for entry in existing_entries
            ):
                errors["base"] = "devices_conflict"
            else:
                # 更新選項
                self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
                return self.async_create_entry(title=None, data=None)

        old_entry_name = self.config_entry.data.get(CONF_ENTRY_NAME, "")

        notify_services = self.hass.services.async_services().get("notify", {})
        mobile_app_devices = [
            devices for devices in notify_services if devices.startswith("mobile_app")
        ]

        old_config = self.config_entry.data.get(CONF_DEVICES, [])
        _old_config = [device_id for device_id in old_config if device_id in mobile_app_devices]

        entity_registry = er.async_get(self.hass)
        person_entities = [
            entity.entity_id for entity in entity_registry.entities.values()
            if entity.entity_id.startswith("person.")
        ]

        schema = vol.Schema({
            vol.Required(CONF_ENTRY_NAME, default=old_entry_name):
            vol.In(person_entities),
            vol.Required(
                CONF_DEVICES,
                default=_old_config,
            ):
            cv.multi_select(mobile_app_devices)
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
