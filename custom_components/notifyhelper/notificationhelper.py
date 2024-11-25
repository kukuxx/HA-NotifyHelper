import asyncio
import aiofiles
import json
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class NotificationHelper:

    def __init__(self, hass, devices):
        self.hass = hass
        self._lock = asyncio.Lock()
        self._notifications_dict: dict[str, list[list, int]] = {}
        self._notify_device_id = devices

    async def save_notifications_dict(self):
        """保存字典"""
        try:
            file_path = "/config/custom_components/notifyhelper/notifications.json"
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                json_data = json.dumps(self._notifications_dict, ensure_ascii=False, indent=4)
                await f.write(json_data)
        except Exception as e:
            _LOGGER.error(f"Save dict Error: {e}")

    async def load_notifications_dict(self):
        """讀取字典"""
        try:
            file_path = "/config/custom_components/notifyhelper/notifications.json"
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                contents = await f.read()
                _dict = json.loads(contents)
            return _dict
        except FileNotFoundError:
            # json不存在
            _dict = {}
            _LOGGER.warning(f"Dict Not Found")
            return _dict
        except json.JSONDecodeError:
            # json格式錯誤
            _dict = {}
            _LOGGER.warning(f"Dict Decode Error")
            return _dict

    async def start(self):
        """初始化,檢查是否有舊資料並建立字典"""
        try:
            old_dict = await self.load_notifications_dict()

            if old_dict:
                self._notifications_dict = old_dict
                # 檢查是否有增加新設備
                for key in self._notify_device_id:
                    self._notifications_dict.setdefault(key, [None, 0])
                # for k in list(self._notifications_dict.keys()):
                #     if k not in self._notify_device_id:
                #         self._notifications_dict.pop(k, None)
            else:
                for key in self._notify_device_id:
                    self._notifications_dict[key] = [None, 0]

            if self._notify_device_id:
                tasks = [
                    self.update_notification_log(device_id) for device_id in self._notify_device_id
                ]
                await asyncio.gather(*tasks)
        except Exception as e:
            _LOGGER.error(f"Initialization dict Error: {e}")

    async def stop(self):
        """刪除sensor"""
        for device_id in self._notify_device_id:
            state_entity_id = f"sensor.{device_id}_log"
            self.hass.states.async_remove(state_entity_id)

    async def send_notification(self, data):
        """發送通知"""
        try:
            save_tasks = []
            update_tasks = []
            if "data" not in data:
                data["data"] = {}
            device_id = data.get("target", None)

            if device_id is None:
                for _device_id in self._notify_device_id:
                    _data = data
                    badge = self._notifications_dict[_device_id][1] + 1
                    _data["data"]["push"] = {
                        "badge": badge,
                    }
                    await self.hass.services.async_call(
                        "notify", _device_id, {
                            "message": _data.get("message", "No message"),
                            "title": _data.get("title", "Notification"),
                            "data": _data["data"]
                        }
                    )
                    save_tasks.append(self.save_notification(_device_id, _data))
                    update_tasks.append(self.update_notification_log(_device_id))

                await asyncio.gather(*save_tasks)
                async with self._lock:
                    await self.save_notifications_dict()
                await asyncio.gather(*update_tasks)

            elif device_id in self._notify_device_id:
                badge = self._notifications_dict[device_id][1] + 1
                data["data"]["push"] = {
                    "badge": badge,
                }
                await self.hass.services.async_call(
                    "notify", device_id, {
                        "message": data.get("message", "No message"),
                        "title": data.get("title", "Notification"),
                        "data": data["data"]
                    }
                )
                await self.save_notification(device_id, data)
                async with self._lock:
                    await self.save_notifications_dict()
                await self.update_notification_log(device_id)
            else:
                _LOGGER.error(
                    f"The device {device_id} does not found. Please check whether the device ID is correct."
                )

        except KeyError as e:
            _LOGGER.error(f"Get dict Error: {e}")
        except Exception as e:
            _LOGGER.error(f"Send notification Error: {e}")

    async def save_notification(self, device_id, data):
        """保存通知"""
        try:
            notifications_list = self._notifications_dict[device_id][0] if self._notifications_dict[
                device_id][0] is not None else []
            time = datetime.now()
            send_time = time.strftime("%Y-%m-%d %H:%M:%S")
            message = data.get("message", "No message")
            title = data.get("title", "Notification")
            image = data.get("data", {}).get("image", None)
            badge = data.get("data") and data["data"].get("push", {}).get("badge", 1) or 1
            color = data.get("color", "#c753e8")
            # 建立通知
            if image is None:
                notification = (
                    f"<ha-alert alert-type='info'><strong>{title}</strong></ha-alert>"
                    f"<blockquote><font color='{color}'>{message}</font><br>"  #Text color can be customized
                    f"<br><b><i>{send_time}</i></b></blockquote>"
                )
            else:
                notification = (
                    f"<ha-alert alert-type='info'><strong>{title}</strong></ha-alert>"
                    f"<blockquote><font color='{color}'>{message}</font><br>"  #Text color can be customized
                    f"<br><img src='{image}'/><br>"
                    f"<br><b><i>{send_time}</i></b></blockquote>"
                )
            # 將新通知加入列表 # Delete the oldest notification when the number of saved notifications is greater than 30
            notifications_list.insert(0, notification)
            if len(notifications_list) > 40:
                notifications_list.pop()
            async with self._lock:
                self._notifications_dict[device_id] = [notifications_list, badge]

        except KeyError as e:
            _LOGGER.error(f"Get dict Error: {e}")
        except Exception as e:
            _LOGGER.error(f"Notification_log Error: {e}")

    async def update_notification_log(self, device_id):
        """將通知列表更新到 sensor"""
        try:
            notification_log = self._notifications_dict[device_id][0]

            if notification_log is not None:
                notification_str = '\n'.join(notification_log)
                # 更新 sensor
                self.hass.states.async_set(
                    f"sensor.{device_id}_log",
                    f"{device_id} notification log",
                    attributes={"notifications": notification_str}
                )
            else:
                self.hass.states.async_set(
                    f"sensor.{device_id}_log", f"{device_id} notification log"
                )
        except Exception as e:
            _LOGGER.error(f"Update notification_log Error: {e}")

    async def read(self, data):
        """改成已讀狀態"""
        device_id = data["target"]
        if device_id in self._notify_device_id:
            await self.read_notification(device_id)
            await self.hass.services.async_call("notify", device_id, {"message": "clear_badge"})
            await self.update_notification_log(device_id)

    async def read_notification(self, device_id):
        """將通知中的 info 類型更改為 success 類型"""
        try:
            notifications_list = self._notifications_dict.get(device_id, [])[0]
            # 如果該通知列表不為空且為列表型態
            if notifications_list and isinstance(notifications_list, list):
                for index, notification in enumerate(notifications_list):
                    if 'alert-type=\'info\'' in notification:
                        # 將 'info' 替換為 'success'
                        new_notification = notification.replace(
                            'alert-type=\'info\'', 'alert-type=\'success\''
                        )
                        notifications_list[index] = new_notification
                async with self._lock:
                    self._notifications_dict[device_id] = [notifications_list, 0]
                    await self.save_notifications_dict()
            else:
                _LOGGER.warning(f"No valid notifications found for {device_id}")

        except Exception as e:
            _LOGGER.error(f"Error replacing notifications: {e}")
