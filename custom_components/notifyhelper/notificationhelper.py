import asyncio
import aiofiles
import json
import logging
import os
import pickle

from collections import deque
from urllib.parse import urlparse

from homeassistant.util.dt import now, as_timestamp

_LOGGER = logging.getLogger(__name__)


class NotificationHelper:

    def __init__(
        self, hass, entry_id, entry_name, ios_devices, android_devices, url
    ):
        self.hass = hass
        self.entry_id = entry_id
        self.entry_name = entry_name.split(".")[1]
        self._lock = asyncio.Lock()
        self._notifications_dict: dict[str, list[deque, int]] = {}
        self._ios_devices_id = ios_devices
        self._android_devices_id = android_devices
        self._url = url
        self.limit = 100

    async def save_notifications_dict(self):
        """保存字典(save dict)"""
        try:
            file_path = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.pkl"
            async with aiofiles.open(file_path, 'wb') as f:
                pkl_data = pickle.dumps(self._notifications_dict)
                await f.write(pkl_data)
            _LOGGER.debug(
                f"Successfully saved notifications dict for {self.entry_name} to {file_path}"
            )
        except (OSError, IOError) as e:
            # 硬碟空間不足
            _LOGGER.error(f"Error saving {self.entry_name} pickle file: {e}")
        except Exception as e:
            _LOGGER.error(f"Save {self.entry_name} dict Error: {e}")

    async def load_notifications_dict(self):
        """讀取字典(load dict)"""
        _dict = {}
        try:
            pkl_file_path = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.pkl"
            json_file_pash = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.json"

            if os.path.exists(pkl_file_path):
                # 優先讀取 Pickle 文件
                async with aiofiles.open(pkl_file_path, 'rb') as f:
                    contents = await f.read()
                    _dict = pickle.loads(contents)
                _LOGGER.debug(
                    f"{self.entry_name}: Notification file loaded successfully."
                )

            elif os.path.exists(json_file_pash):
                async with aiofiles.open(
                    json_file_pash, 'r', encoding='utf-8'
                ) as f:
                    contents = await f.read()
                    _dict = json.loads(contents)
                _LOGGER.debug(
                    f"{self.entry_name}: Notification file loaded successfully."
                )
            else:
                _LOGGER.debug(
                    f"{self.entry_name}: No notification file found."
                )

        except (EOFError, pickle.UnpicklingError) as e:
            # 文件損壞
            _LOGGER.error(f"Error reading {self.entry_name} pickle file: {e}")
        except json.JSONDecodeError as e:
            # json格式錯誤
            _LOGGER.error(f"{self.entry_name} Json Decode Error: {e}")

        return _dict

    async def start(self):
        """檢查是否有舊資料並建立字典(Check if there are old data and build a dict)"""
        try:
            old_dict = await self.load_notifications_dict()

            if old_dict:
                notifications = old_dict[self.entry_id][0]
                badge = old_dict[self.entry_id][1]
                self._notifications_dict[self.entry_id] = [
                    deque(notifications, maxlen=self.limit), badge
                ]
            else:
                self._notifications_dict[self.entry_id
                                         ] = [deque(maxlen=self.limit), 0]

            await self.update_notification_log()

        except Exception as e:
            _LOGGER.error(f"Initialization {self.entry_name} dict Error: {e}")

    async def stop(self):
        """刪除sensor(remove sensor)"""
        try:
            state_entity_id = f"sensor.{self.entry_name}_notifications"
            self.hass.states.async_remove(state_entity_id)
        except Exception as e:
            _LOGGER.error(f"Remove {self.entry_name} sensor Error: {e}")

    async def send_notification(self, data):
        """發送通知(send notification)"""

        async def _send_to_devices(devices, p_data):
            if not devices:
                return []

            if self._url:
                p_data.setdefault("url", self._url)

            notification_payload = {
                "message": message,
                "title": title,
                "data": p_data,
            }

            return [
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "notify", device_id, notification_payload
                    )
                ) for device_id in devices
            ]

        try:
            async with self._lock:
                _data = dict(data)
                _LOGGER.debug(f"{self.entry_name}: {_data}")

                _data.setdefault("title", "Notification")
                _data.setdefault("message", "No message")
                parameters_data = _data.setdefault("data", {})
                badge = self._notifications_dict[self.entry_id][1] + 1
                message = _data["message"]
                title = _data["title"]

                tasks = []

                if "android" not in parameters_data and "ios" not in parameters_data:
                    image = parameters_data.get("image")
                    video = parameters_data.get("video")
                    parameters_data.setdefault("push",
                                               {}).update({"badge": badge})
                    tasks = await _send_to_devices(
                        self._ios_devices_id + self._android_devices_id,
                        parameters_data
                    )
                else:
                    android_data = parameters_data.get("android")
                    ios_data = parameters_data.get("ios")
                    image = (android_data and android_data.get("image")) or \
                            (ios_data and ios_data.get("image"))
                    video = (android_data and android_data.get("video")) or \
                            (ios_data and ios_data.get("video"))

                    if android_data:
                        android_tasks = await _send_to_devices(
                            self._android_devices_id, android_data
                        )
                        tasks.extend(android_tasks)

                    if ios_data:
                        ios_data.setdefault("push",
                                            {}).update({"badge": badge})
                        ios_tasks = await _send_to_devices(
                            self._ios_devices_id, ios_data
                        )
                        tasks.extend(ios_tasks)

                if tasks:
                    await asyncio.gather(*tasks)

                await self.save_notification(_data, badge, image, video)
                await self.save_notifications_dict()
                await self.update_notification_log()

        except KeyError as e:
            _LOGGER.error(f"Get {self.entry_name} data error: {e}")
        except Exception as e:
            _LOGGER.error(
                f"Failed to send notification for {self.entry_name}: {e}"
            )

    async def save_notification(self, data, badge, image, video):
        """保存通知 (save notification)"""
        try:
            notifications_dq = self._notifications_dict[self.entry_id][0]
            timestamp = as_timestamp(now())
            send_time = now().strftime("%Y-%m-%d %H:%M:%S")
            message = data["message"]
            title = data["title"]
            color = data.get("color", None)

            message_html = f"<font color='{color}'>{message}</font>" if color else message
            notification_parts = [
                f"<ha-alert alert-type='info'><strong>{title}</strong></ha-alert>",
                f"<blockquote>{message_html}",
            ]

            if image:
                _, url_bool = self.check_url(image)
                timestamp_suffix = "" if url_bool else f"?timestamp={timestamp}"
                notification_parts.append(
                    f"<br><br><img src='{image}{timestamp_suffix}'/>"
                )

            if video:
                video_type, url_bool = self.check_url(video)
                timestamp_suffix = "" if url_bool else f"?timestamp={timestamp}"
                notification_parts.append(
                    f"<br><br><video controls preload='metadata'>"
                    f"<source src='{video}{timestamp_suffix}' type='video/{video_type}'>"
                    f"</video>"
                )

            notification_parts.append(
                f"<br><br><b><i>{send_time}</i></b></blockquote>"
            )
            # 添加通知並更新 badge
            notifications_dq.appendleft("".join(notification_parts))
            self._notifications_dict[self.entry_id][1] = badge

        except Exception as e:
            _LOGGER.error(f"Save {self.entry_name} notification Error: {e}")

    def check_url(self, url):
        """check url"""
        valid_extensions = {
            "mp4", "avi", "mov", "png", "jpg", "jpeg", "gif", "webp"
        }
        result = urlparse(url)
        url_bool = result.scheme in ['http', 'https']
        path = result.path
        file_type = path.split('.')[-1].lower() \
                    if '.' in path and path.split('.')[-1].lower() in valid_extensions else None
        return file_type, url_bool

    async def update_notification_log(self):
        """將通知列表更新到sensor(update sensor)"""
        try:
            notification_dq = self._notifications_dict[self.entry_id][0]

            if notification_dq:
                # notification_str = '\n'.join(notification_dq)
                # 更新 sensor
                self.hass.states.async_set(
                    f"sensor.{self.entry_name}_notifications",
                    f"{self.entry_name} notifications",
                    attributes={"notifications": list(notification_dq)}
                )
                _LOGGER.debug(
                    f"{self.entry_name}:Notification updated successfully"
                )
            else:
                self.hass.states.async_set(
                    f"sensor.{self.entry_name}_notifications",
                    f"{self.entry_name} notifications",
                    attributes={"notifications": []}
                )
                _LOGGER.debug(
                    f"{self.entry_name}:Notification is emty updated successfully"
                )
        except Exception as e:
            _LOGGER.error(f"Update {self.entry_name} notifications Error: {e}")

    async def read(self, data):
        """改成已讀狀態(change to read status)"""
        await self.read_notification()

        if self._ios_devices_id:
            tasks = [
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "notify", device_id, {"message": "clear_badge"}
                    )
                ) for device_id in self._ios_devices_id
            ]

        _LOGGER.debug(f"Read successfully")

    async def read_notification(self):
        """將通知中的 info 類型更改為 success 類型(change alert-type info to success)"""
        try:
            async with self._lock:
                notifications_dq = self._notifications_dict[self.entry_id][0]
                # 如果該通知不為空
                if notifications_dq:
                    notifications_dq = [
                        notification.replace(
                            'alert-type=\'info\'', 'alert-type=\'success\''
                        ) if 'alert-type=\'info\'' in notification else
                        notification for notification in notifications_dq
                    ]
                    self._notifications_dict[self.entry_id] = [
                        deque(notifications_dq, maxlen=self.limit), 0
                    ]
                    await self.save_notifications_dict()
                    await self.update_notification_log()
                else:
                    _LOGGER.warning(
                        f"No valid notifications found for {self.entry_name}"
                    )
        except Exception as e:
            _LOGGER.error(
                f"Error replacing {self.entry_name} notifications: {e}"
            )

    async def clear(self, data):
        """清空通知(clear notifications)"""
        try:
            async with self._lock:
                notifications_dq = self._notifications_dict[self.entry_id][0]
                if notifications_dq:
                    notifications_dq.clear()
                    self._notifications_dict[self.entry_id][1] = 0
                    await self.save_notifications_dict()
                    await self.update_notification_log()
                else:
                    _LOGGER.warning(
                        f"No valid notifications found for {self.entry_name}"
                    )

            if self._ios_devices_id:
                tasks = [
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            "notify", device_id, {"message": "clear_badge"}
                        )
                    ) for device_id in self._ios_devices_id
                ]

            _LOGGER.debug(f"Clear successfully")
        except Exception as e:
            _LOGGER.error(
                f"Error clearing {self.entry_name} notifications: {e}"
            )
