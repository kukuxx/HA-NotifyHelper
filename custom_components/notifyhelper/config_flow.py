import logging

import voluptuous as vol

from itertools import chain

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    CONF_IOS_DEVICES,
    CONF_ANDROID_DEVICES,
    CONF_ENTRY_NAME,
    CONF_URL,
)

_LOGGER = logging.getLogger(__name__)
TEXT_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))


class NotifyHelperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NotifyHelper."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return NotifyHelperOptionsFlow()

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration step."""
        errors = {}

        current_entries = self._async_current_entries()
        entry_names = {entry.data.get(CONF_ENTRY_NAME) for entry in current_entries}
        devices = set(chain.from_iterable(
            entry.data.get(CONF_IOS_DEVICES, []) + entry.data.get(CONF_ANDROID_DEVICES, [])
            for entry in current_entries
        ))


        if user_input is not None:
            # 驗證名稱是否已存在
            if user_input[CONF_ENTRY_NAME] in entry_names:
                errors["base"] = "name_exists"
            else:
                input_ios = user_input.get(CONF_IOS_DEVICES, [])
                input_android = user_input.get(CONF_ANDROID_DEVICES, [])
                # 驗證是否至少選擇一個設備和設備是否重複
                if not (input_devices := set(input_ios + input_android)):
                    errors["base"] = "no_device"
                elif len(input_devices) != len(input_ios + input_android):
                    errors["base"] = "devices_conflict"
                elif input_devices & devices:
                    errors["base"] = "devices_conflict"
                elif (input_url := user_input.get(CONF_URL)) and not input_url.startswith('/'):
                    errors["base"] = "url_error"
                else:
                    # 保存配置
                    return self.async_create_entry(
                        title=user_input[CONF_ENTRY_NAME],
                        data=user_input,
                    )

        # 取得所有 notify domain的服務
        notify_services = self.hass.services.async_services().get("notify", {})
        mobile_app_devices = [
            device for device in notify_services if device.startswith("mobile_app")
        ]

        person_entities = self.hass.states.async_entity_ids("person")

        # Schema
        schema = vol.Schema(
            {
                vol.Required(CONF_ENTRY_NAME):
                vol.In(person_entities),
                vol.Optional(CONF_URL):
                TEXT_SELECTOR,
                vol.Required(CONF_IOS_DEVICES, default=[]):
                cv.multi_select(mobile_app_devices),
                vol.Required(CONF_ANDROID_DEVICES, default=[]):
                cv.multi_select(mobile_app_devices),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


class NotifyHelperOptionsFlow(config_entries.OptionsFlow):
    """Handle options for NotifyHelper."""

    async def async_step_init(self, user_input=None):
        """Manage the options for NotifyHelper."""
        errors = {}

        existing_entries = [
            entry for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.entry_id != self._config_entry_id
        ]
        entry_names = {entry.data.get(CONF_ENTRY_NAME) for entry in existing_entries}
        devices = set(chain.from_iterable(
            entry.data.get(CONF_IOS_DEVICES, []) + entry.data.get(CONF_ANDROID_DEVICES, [])
            for entry in existing_entries
        ))

        if user_input is not None:
            # 驗證名稱是否已存在
            if user_input[CONF_ENTRY_NAME] in entry_names:
                errors["base"] = "name_exists"
            else:
                input_ios = user_input.get(CONF_IOS_DEVICES, [])
                input_android = user_input.get(CONF_ANDROID_DEVICES, [])
                # 驗證是否至少選擇一個設備和設備是否重複
                if not (input_devices := set(input_ios + input_android)):
                    errors["base"] = "no_device"
                elif len(input_devices) != len(input_ios + input_android):
                    errors["base"] = "devices_conflict"
                elif input_devices & devices:
                    errors["base"] = "devices_conflict"
                elif (input_url := user_input.get(CONF_URL)) and not input_url.startswith('/'):
                    errors["base"] = "url_error"
                else:
                    # 更新選項
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=user_input
                    )
                    return self.async_create_entry(title=None, data=None)

        old_entry_name = self.config_entry.data.get(CONF_ENTRY_NAME)
        old_url = self.config_entry.data.get(CONF_URL, "")
        person_entities = self.hass.states.async_entity_ids("person")

        notify_services = self.hass.services.async_services().get("notify", {})
        mobile_app_devices = [
            devices for devices in notify_services if devices.startswith("mobile_app")
        ]
        old_ios_devices = [
            ios_device for ios_device in self.config_entry.data.get(CONF_IOS_DEVICES, [])
            if ios_device in mobile_app_devices
        ]

        old_android_devices = [
            android_device
            for android_device in self.config_entry.data.get(CONF_ANDROID_DEVICES, [])
            if android_device in mobile_app_devices
        ]

        schema = vol.Schema(
            {
                vol.Required(CONF_ENTRY_NAME, default=old_entry_name):
                vol.In(person_entities),
                vol.Optional(CONF_URL, default=old_url):
                TEXT_SELECTOR,
                vol.Required(CONF_IOS_DEVICES, default=old_ios_devices):
                cv.multi_select(mobile_app_devices),
                vol.Required(CONF_ANDROID_DEVICES, default=old_android_devices):
                cv.multi_select(mobile_app_devices),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
