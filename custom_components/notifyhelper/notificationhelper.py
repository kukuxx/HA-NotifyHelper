import asyncio
import aiofiles
import json
import logging

from homeassistant.util.dt import now

_LOGGER = logging.getLogger(__name__)


class NotificationHelper:

    def __init__(self, hass, devices, entry_id, entry_name):
        self.hass = hass
        self._lock = asyncio.Lock()
        self._notifications_dict: dict[str, list[list, int]] = {}
        self._notify_device_id = devices
        self.entry_id = entry_id
        self.entry_name = entry_name.split(".")[1]

    async def save_notifications_dict(self):
        """保存字典(save dict)"""
        try:
            file_path = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.json"
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                json_data = json.dumps(self._notifications_dict, ensure_ascii=False, indent=4)
                await f.write(json_data)
        except Exception as e:
            _LOGGER.error(f"Save dict Error: {e}")

    async def load_notifications_dict(self):
        """讀取字典(load dict)"""
        try:
            file_path = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.json"
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                contents = await f.read()
                _dict = json.loads(contents)
            return _dict
        except FileNotFoundError:
            # json不存在
            _dict = {}
            # _LOGGER.warning(f"Dict Not Found")
            return _dict
        except json.JSONDecodeError:
            # json格式錯誤
            _dict = {}
            _LOGGER.warning(f"Dict Decode Error")
            return _dict

    async def start(self):
        """檢查是否有舊資料並建立字典(Check if there are old data and build a dict)"""
        try:
            old_dict = await self.load_notifications_dict()

            if old_dict:
                self._notifications_dict = old_dict
            else:
                self._notifications_dict[self.entry_id] = [None, 0]

            await self.update_notification_log()

        except Exception as e:
            _LOGGER.error(f"Initialization dict Error: {e}")

    async def stop(self):
        """刪除sensor(remove sensor)"""
        try:
            state_entity_id = f"sensor.{self.entry_name}_notifications"
            self.hass.states.async_remove(state_entity_id)
        except Exception as e:
            _LOGGER.error(f"Remove sensor Error: {e}")

    async def send_notification(self, data):
        """發送通知(send notification)"""
        try:
            _data = dict(data)
            _LOGGER.debug(f"{_data}")
            if "data" not in _data:
                _data["data"] = {}
                _LOGGER.debug(f"{_data}")
            if "push" not in _data["data"]:
                _data["data"]["push"] = {}
                _LOGGER.debug(f"{_data}")

            badge = self._notifications_dict[self.entry_id][1] + 1
            _data["data"]["push"].update({
                "badge": badge,
            })
            _LOGGER.debug(f"{_data}")

            for device_id in self._notify_device_id:
                await self.hass.services.async_call(
                    "notify", device_id, {
                        "message": _data.get("message", "No message"),
                        "title": _data.get("title", "Notification"),
                        "data": _data["data"]
                    }
                )
            await self.save_notification(_data)
            async with self._lock:
                await self.update_notification_log()
                await self.save_notifications_dict()
        except KeyError as e:
            _LOGGER.error(f"Get dict Error: {e}")
        except Exception as e:
            _LOGGER.error(f"Send notification Error: {e}")

    async def save_notification(self, data):
        """保存通知(save notification)"""
        try:
            notifications_list = self._notifications_dict[
                self.entry_id][0] if self._notifications_dict[self.entry_id][0] is not None else []

            send_time = now().strftime("%Y-%m-%d %H:%M:%S")
            message = data.get("message", "No message")
            title = data.get("title", "Notification")
            image = data.get("data", {}).get("image", None)
            video = data.get("data", {}).get("video", None)
            badge = data.get("data") and data["data"].get("push", {}).get("badge", 1) or 1
            color = data.get("color", None)
            # 建立通知
            notification = (f"<ha-alert alert-type='info'><strong>{title}</strong></ha-alert>")

            if color is None:
                notification += f"<blockquote>{message}<br>"
            else:
                notification += f"<blockquote><font color='{color}'>{message}</font><br>"
            if image is not None:
                notification += f"<br><img src='{image}'/><br>"
            elif video is not None:
                notification += f"<br><a href='{video}'>Show Video</a><br>"

            notification += f"<br><b><i>{send_time}</i></b></blockquote>"

            # 將新通知加入列表 #
            notifications_list.insert(0, notification)
            if len(notifications_list) > 100:
                notifications_list.pop()
            async with self._lock:
                self._notifications_dict[self.entry_id] = [notifications_list, badge]

        except KeyError as e:
            _LOGGER.error(f"Get dict Error: {e}")
        except Exception as e:
            _LOGGER.error(f"Notification_log Error: {e}")

    async def update_notification_log(self):
        """將通知列表更新到sensor(update sensor)"""
        try:
            notification_log = self._notifications_dict[self.entry_id][0]

            if notification_log is not None:
                notification_str = '\n'.join(notification_log)
                # 更新 sensor
                self.hass.states.async_set(
                    f"sensor.{self.entry_name}_notifications",
                    f"{self.entry_name} notifications",
                    attributes={"notifications": notification_str}
                )
            else:
                self.hass.states.async_set(
                    f"sensor.{self.entry_name}_notifications", f"{self.entry_name} notifications"
                )
        except Exception as e:
            _LOGGER.error(f"Update notifications_log Error: {e}")

    async def read(self, data):
        """改成已讀狀態(change to read status)"""
        async with self._lock:
            await self.read_notification()
            await self.update_notification_log()
        for device_id in self._notify_device_id:
            await self.hass.services.async_call("notify", device_id, {"message": "clear_badge"})

    async def read_notification(self):
        """將通知中的 info 類型更改為 success 類型(change alert-type info to success)"""
        try:
            notifications_list = self._notifications_dict.get(self.entry_id)[0]
            # 如果該通知列表不為空且為列表型態
            if notifications_list and isinstance(notifications_list, list):
                for index, notification in enumerate(notifications_list):
                    if 'alert-type=\'info\'' in notification:
                        # 將 'info' 替換為 'success'
                        new_notification = notification.replace(
                            'alert-type=\'info\'', 'alert-type=\'success\''
                        )
                        notifications_list[index] = new_notification

                self._notifications_dict[self.entry_id] = [notifications_list, 0]
                await self.save_notifications_dict()
            else:
                _LOGGER.warning(f"No valid notifications found for {self.entry_name}")
        except Exception as e:
            _LOGGER.error(f"Error replacing notifications: {e}")
