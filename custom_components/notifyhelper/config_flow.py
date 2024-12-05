import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CONF_IOS_DEVICES, CONF_ANDROID_DEVICES, CONF_ENTRY_NAME

_LOGGER = logging.getLogger(__name__)


class NotifyHelperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NotifyHelper."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration step."""
        errors = {}

        current_entries = self._async_current_entries()
        entry_names_set = set()
        ios_devices_set = set()
        android_devices_set = set()

        for entry in current_entries:
            entry_names_set.add(entry.data.get(CONF_ENTRY_NAME))
            ios_devices_set.update(entry.data.get(CONF_IOS_DEVICES, []))
            android_devices_set.update(entry.data.get(CONF_ANDROID_DEVICES, []))

        devices_set = ios_devices_set | android_devices_set

        if user_input is not None:
            # 驗證名稱是否已存在
            if user_input[CONF_ENTRY_NAME] in entry_names_set:
                errors["base"] = "name_exists"
            else:
                input_ios_set = set(user_input.get(CONF_IOS_DEVICES, []))
                input_android_set = set(user_input.get(CONF_ANDROID_DEVICES, []))
                # 驗證是否至少選擇一個設備和設備是否重複
                if not input_ios_set and not input_android_set:
                    errors["base"] = "no_device"
                elif (
                    input_ios_set & devices_set or input_android_set & devices_set
                    or input_ios_set & input_android_set
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
            device for device in notify_services if device.startswith("mobile_app")
        ]

        entity_registry = er.async_get(self.hass)
        entities = entity_registry.entities.values()
        person_entities = list(
            map(
                lambda entity: entity.entity_id,
                filter(lambda e: e.entity_id.startswith("person."), entities)
            )
        )

        # Schema
        schema = vol.Schema({
            vol.Required(CONF_ENTRY_NAME):
            vol.In(person_entities),
            vol.Required(CONF_IOS_DEVICES, default=[]):
            cv.multi_select(mobile_app_devices),
            vol.Required(CONF_ANDROID_DEVICES, default=[]):
            cv.multi_select(mobile_app_devices),
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
        entry_names_set = set()
        ios_devices_set = set()
        android_devices_set = set()

        for entry in existing_entries:
            entry_names_set.add(entry.data.get(CONF_ENTRY_NAME))
            ios_devices_set.update(entry.data.get(CONF_IOS_DEVICES, []))
            android_devices_set.update(entry.data.get(CONF_ANDROID_DEVICES, []))

        devices_set = ios_devices_set | android_devices_set

        if user_input is not None:
            # 驗證名稱是否已存在
            if user_input[CONF_ENTRY_NAME] in entry_names_set:
                errors["base"] = "name_exists"
            else:
                input_ios_set = set(user_input.get(CONF_IOS_DEVICES, []))
                input_android_set = set(user_input.get(CONF_ANDROID_DEVICES, []))
                # 驗證是否至少選擇一個設備和設備是否重複
                if not input_ios_set and not input_android_set:
                    errors["base"] = "no_device"
                elif (
                    input_ios_set & devices_set or input_android_set & devices_set
                    or input_ios_set & input_android_set
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
        old_ios_devices = [
            device_id for device_id in self.config_entry.data.get(CONF_IOS_DEVICES, [])
            if device_id in mobile_app_devices
        ]
        old_android_devices = [
            device_id for device_id in self.config_entry.data.get(CONF_ANDROID_DEVICES, [])
            if device_id in mobile_app_devices
        ]

        entity_registry = er.async_get(self.hass)
        entities = entity_registry.entities.values()
        person_entities = list(
            map(
                lambda entity: entity.entity_id,
                filter(lambda e: e.entity_id.startswith("person."), entities)
            )
        )

        schema = vol.Schema({
            vol.Required(CONF_ENTRY_NAME, default=old_entry_name):
            vol.In(person_entities),
            vol.Required(CONF_IOS_DEVICES, default=old_ios_devices):
            cv.multi_select(mobile_app_devices),
            vol.Required(CONF_ANDROID_DEVICES, default=old_android_devices):
            cv.multi_select(mobile_app_devices),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
