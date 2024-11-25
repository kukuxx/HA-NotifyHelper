import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_DEVICES


class NotifyHelperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NotifyHelper."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration step."""
        errors = {}

        if user_input is not None:
            # 驗證至少選擇一項
            if not user_input[CONF_DEVICES]:
                errors["base"] = "invalid"  # 顯示錯誤提示
            else:
                # 保存配置
                return self.async_create_entry(
                    title="NotifyHelper Configuration",
                    data=user_input,
                )

        # 取得所有 notify domain的服務
        notify_services = self.hass.services.async_services().get("notify", {})
        mobile_app_devices = [
            devices for devices in notify_services if devices.startswith("mobile_app")
        ]

        schema = vol.Schema({
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

        if user_input is not None:
            if not user_input[CONF_DEVICES]:
                errors["base"] = "invalid"  # 顯示錯誤提示
            else:
                # 更新選項
                return self.async_create_entry(title="", data=user_input)

        notify_services = self.hass.services.async_services().get("notify", {})
        mobile_app_devices = [
            devices for devices in notify_services if devices.startswith("mobile_app")
        ]

        old_config = self.config_entry.options.get(
            CONF_DEVICES, self.config_entry.data.get(CONF_DEVICES, [])
        )
        _old_config = [device_id for device_id in old_config if device_id in mobile_app_devices]

        schema = vol.Schema({
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
